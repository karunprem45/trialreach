"""Site Scout: a short tool-calling agent on top of deserts.py (no Streamlit imports).

run_scout() asks the LLM to call the tools below (max MAX_TOOL_CALLS). With no key, or on any
LLM error, it runs the same tools in a fixed order and labels the run "offline mode".
Scores places, never people. Every number in the final answer comes from tool results.
"""
import json
import re

import deserts as ds
import llm

MAX_TOOL_CALLS = 6
OFFLINE_LABEL = "offline mode"

# Words that suggest a person is told they qualify. Such an answer is replaced by the template.
QUALIFY = re.compile(r"qualif|eligib", re.I)
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")

# Extra words that point to a disease (labels and ids are matched too).
DISEASE_WORDS = {"hypertension": "BPHIGH", "blood pressure": "BPHIGH", "heart": "CHD",
                 "lung": "COPD", "sugar": "DIABETES"}

SYSTEM = f"""You are Site Scout, an assistant for a clinical research office in Massachusetts.
Goal: recommend which county and hospital should open the next trial site for the disease asked about.
Use the tools: rank_counties first, then county_details for the worst county, then
simulate_new_site for one top hospital, then write_outreach_flyer. Use at most {MAX_TOOL_CALLS} tool calls.
Rules:
- Use only numbers that appear in tool results. Do not invent or recompute numbers.
- Never say a person qualifies for a trial or give medical advice. Say "talk to your doctor or the study team".
- Mention that trial details are on ClinicalTrials.gov.
- Final answer: short plain text with the county, the hospital, the before and after score,
  who to reach, and why. No emojis. No numbered lists."""

FLYER_SYSTEM = """You write a short resident flyer for a clinical research office in Massachusetts.
Use only the facts given. Do not invent numbers, trials or phone numbers.
Never say the reader qualifies for a trial; say "talk to your doctor or the study team".
Mention that trial details are on ClinicalTrials.gov. Plain language, grade 6, at most 120 words,
in the requested language. Output only the flyer text."""

TOOLS = [
    {"type": "function", "function": {
        "name": "rank_counties",
        "description": "Rank Massachusetts counties for a disease, worst research desert first. Returns the top 5.",
        "parameters": {"type": "object", "properties": {
            "disease": {"type": "string", "description": "Disease name, e.g. Diabetes, Asthma, Cancer"}},
            "required": ["disease"]}}},
    {"type": "function", "function": {
        "name": "county_details",
        "description": "Top hospitals, nearest recruiting trials and outreach towns for one county.",
        "parameters": {"type": "object", "properties": {
            "county": {"type": "string"}, "disease": {"type": "string"}},
            "required": ["county", "disease"]}}},
    {"type": "function", "function": {
        "name": "simulate_new_site",
        "description": "What-if: add one trial site at a hospital and return the score and rank before and after.",
        "parameters": {"type": "object", "properties": {
            "county": {"type": "string"}, "hospital": {"type": "string", "description": "Hospital name from county_details"},
            "disease": {"type": "string"}},
            "required": ["county", "hospital", "disease"]}}},
    {"type": "function", "function": {
        "name": "write_outreach_flyer",
        "description": "Draft a short resident flyer for a county and disease.",
        "parameters": {"type": "object", "properties": {
            "county": {"type": "string"}, "disease": {"type": "string"},
            "language": {"type": "string", "description": "English, Spanish, Portuguese, Haitian Creole or Chinese"}},
            "required": ["county", "disease", "language"]}}},
]


def _pretty(x):
    return str(x).title()


def pick_disease(question):
    """Measure id for the disease named in the question. Defaults to DIABETES."""
    q = question.lower()
    for mid, label in ds.CONDITIONS.items():
        if label.lower() in q or re.search(rf"\b{mid.lower()}\b", q):
            return mid
    return next((mid for word, mid in DISEASE_WORDS.items() if word in q), "DIABETES")


class Toolbox:
    """The four tools. `scores` is any function mid -> (counties, towns, sites), so the app can pass
    its cached version. use_llm=False makes the flyer a fixed template (offline mode)."""

    def __init__(self, d, scores=None, use_llm=True):
        self.d, self.use_llm = d, use_llm
        self._scores = scores or (lambda mid: ds.county_scores(d, mid))
        self._memo = {}

    # -- helpers --
    def _get(self, disease):
        text = str(disease).strip()
        mid = next((m for m, lab in ds.CONDITIONS.items()
                    if text.upper() == m or text.lower() == lab.lower()), None)
        if mid is None:
            raise ValueError(f"Unknown disease '{disease}'. Choose one of: "
                             + ", ".join(ds.CONDITIONS.values()))
        if mid not in self._memo:
            self._memo[mid] = self._scores(mid)
        return mid, *self._memo[mid]

    def _row(self, counties, county):
        hit = counties[counties["county"] == str(county).strip().upper()]
        if hit.empty:
            raise ValueError(f"Unknown county '{county}'.")
        return int(hit.index[0]) + 1, hit.iloc[0]

    def _hospitals(self, county, sites):
        h = ds.candidate_hospitals(self.d, county, sites)
        return h.dropna(subset=["lat", "lon"])  # only mappable hospitals can be simulated

    # -- tools --
    def rank_counties(self, disease):
        mid, counties, _, _ = self._get(disease)
        top = counties.head(5)
        return {"disease": ds.CONDITIONS[mid], "counties": [
            {"county": _pretty(r.county), "score": int(r.score),
             "people_per_trial": int(round(r.people_per_trial)),
             "prevalence_pct": round(float(r.prevalence), 1),
             "trials_in_reach": round(float(r.trials_in_reach), 1)} for r in top.itertuples()]}

    def county_details(self, county, disease):
        mid, counties, _, sites = self._get(disease)
        rank, row = self._row(counties, county)
        hosp = self._hospitals(row["county"], sites).head(3)
        near = ds.nearest_trials(self.d, row["county"], sites, n=3)
        _, ej_towns = ds.ej_summary(self.d, row["county"])
        return {
            "county": _pretty(row["county"]), "disease": ds.CONDITIONS[mid], "rank": rank,
            "score": int(row["score"]), "people_per_trial": int(round(row["people_per_trial"])),
            "prevalence_pct": round(float(row["prevalence"]), 1),
            "trials_in_reach": round(float(row["trials_in_reach"]), 1), "reach_miles": ds.REACH_MILES,
            "top_hospitals": [
                {"name": r.FACILITY_NAME, "town": _pretty(r.MUNICIPALITY), "beds": int(r.beds),
                 "nearest_trial_miles": round(float(r.nearest_trial_miles), 1)}
                for r in hosp.itertuples()],
            "nearest_trials": [
                {"nct": r.nct, "title": r.title[:90], "miles": round(float(r.miles), 1)}
                for r in near.itertuples()],
            "outreach_towns": [
                {"town": _pretty(r.town), "ej_residents": int(r.ej_pop),
                 "limited_english_pct": round(float(r.limited_english_pct))}
                for r in ej_towns.head(3).itertuples()]}

    def simulate_new_site(self, county, hospital, disease):
        mid, counties, _, sites = self._get(disease)
        self._row(counties, county)
        h = self._hospitals(county, sites)
        hit = h[h["FACILITY_NAME"].str.lower().str.contains(str(hospital).strip().lower(), regex=False)]
        if hit.empty:
            raise ValueError(f"Hospital '{hospital}' is not a candidate in {_pretty(county)} County.")
        hit = hit.iloc[0]
        before, after = ds.simulate_new_site(
            self.d, mid, float(hit["lat"]), float(hit["lon"]), hit["FACILITY_NAME"])
        b = before.set_index("county").loc[str(county).strip().upper()]
        a = after.set_index("county").loc[str(county).strip().upper()]
        return {
            "county": _pretty(county), "hospital": hit["FACILITY_NAME"],
            "town": _pretty(hit["MUNICIPALITY"]), "disease": ds.CONDITIONS[mid],
            "score_before": int(b["score"]), "score_after": int(a["score"]),
            "rank_before": int(b["rank"]), "rank_after": int(a["rank"]),
            "residents_newly_within_25_miles": int(after["newly_reached"].sum())}

    def write_outreach_flyer(self, county, disease, language):
        mid, counties, _, _ = self._get(disease)
        _, row = self._row(counties, county)
        label, name = ds.CONDITIONS[mid], _pretty(row["county"])
        facts = (f"County: {name}. Disease: {label}. About {row['prevalence']:.1f}% of adults. "
                 f"Few recruiting studies are nearby. Language: {language}.")
        text = llm.generate(facts, FLYER_SYSTEM) if self.use_llm else None
        if text:
            return {"county": name, "language": language, "source": "ai", "text": text}
        text = (f"{label} is common in {name} County: about {row['prevalence']:.1f}% of adults. "
                f"There are few research studies nearby. Studies that are recruiting are listed "
                f"on ClinicalTrials.gov. If you want to know more, talk to your doctor or the study team. "
                f"This is not medical advice.")
        return {"county": name, "language": "English", "source": "template", "text": text}

    def run(self, name, args):
        """Run one tool by name. Always returns a JSON-safe dict; problems become {"error": ...}."""
        try:
            if name not in {t["function"]["name"] for t in TOOLS}:
                raise ValueError(f"Unknown tool '{name}'.")
            result = getattr(self, name)(**args)
            json.dumps(result)
            return result
        except Exception as e:  # bad arguments, unknown county, etc.
            return {"error": str(e)}


# ---------- summaries and the final answer ----------
def summarize(name, r):
    """One short line for a step."""
    if "error" in r:
        return f"Error: {r['error']}"
    if name == "rank_counties":
        c = r["counties"][0]
        return (f"Worst for {r['disease'].lower()}: {c['county']} (score {c['score']}, "
                f"{c['people_per_trial']:,} adults per nearby trial)")
    if name == "county_details":
        h = r["top_hospitals"][0]["name"] if r["top_hospitals"] else "no candidate hospital"
        return f"{r['county']}: {len(r['nearest_trials'])} nearest trials, top hospital {h}"
    if name == "simulate_new_site":
        return (f"{r['hospital']}: score {r['score_before']} to {r['score_after']}, "
                f"{r['residents_newly_within_25_miles']:,} residents newly within 25 miles")
    return f"Flyer drafted for {r['county']} County ({r['language']}, {r['source']})"


def template_answer(steps):
    """Deterministic recommendation built only from tool results."""
    res = {s["tool"]: s["result"] for s in steps if "error" not in s["result"]}
    det = res.get("county_details")
    if not det:
        return "Site Scout could not complete the analysis. Try again or use the County brief tab."
    parts = [
        f"**Recommendation: {det['county']} County.** About {det['prevalence_pct']}% of adults have "
        f"{det['disease'].lower()}, and there are about {det['people_per_trial']:,} adults per nearby "
        f"recruiting trial (research desert score {det['score']} of 100, rank {det['rank']})."]
    sim = res.get("simulate_new_site")
    if sim:
        parts.append(
            f"**Where:** {sim['hospital']} in {sim['town']}. A new study there would move the county's "
            f"score from {sim['score_before']} to {sim['score_after']} (rank {sim['rank_before']} to "
            f"{sim['rank_after']}) and bring {sim['residents_newly_within_25_miles']:,} residents "
            f"within {ds.REACH_MILES} miles of a trial.")
    elif det["top_hospitals"]:
        h = det["top_hospitals"][0]
        parts.append(f"**Where:** {h['name']} in {h['town']} has {h['beds']} licensed beds.")
    if det["outreach_towns"]:
        t = det["outreach_towns"][0]
        parts.append(
            f"**Who to reach:** start in {t['town']}, where {t['ej_residents']:,} residents live in "
            f"environmental-justice neighborhoods and about {t['limited_english_pct']}% of households "
            f"have limited English.")
    parts.append("Trial details are on ClinicalTrials.gov. Residents should talk to their doctor or "
                 "the study team. This is a place-level estimate, not medical advice.")
    return "\n\n".join(parts)


def answer_is_safe(answer, steps, question=""):
    """True if the answer never says a person qualifies and cites only numbers from tool results."""
    if not answer or QUALIFY.search(answer):
        return False
    source = question + " " + " ".join(json.dumps(s["result"]) for s in steps)
    allowed = [float(n.replace(",", "")) for n in NUMBER.findall(source)]
    text = re.sub(r"(?m)^\s*\d+[.)]\s", "", answer)  # ignore list markers
    for lit in NUMBER.findall(text):
        lit = lit.rstrip(",")
        decimals = len(lit.split(".")[1]) if "." in lit else 0
        x = float(lit.replace(",", ""))
        if not any(abs(x - y) <= 0.5 * 10 ** -decimals + 1e-9 for y in allowed):
            return False
    return True


# ---------- agent ----------
def _record(tb, steps, name, args, on_step):
    result = tb.run(name, args)
    step = {"tool": name, "args": args, "summary": summarize(name, result), "result": result}
    steps.append(step)
    if on_step:
        on_step(step)
    return result


def fallback(d, question="", scores=None, on_step=None):
    """Fixed order: worst county, details, simulate top hospital, flyer. Needs no LLM."""
    tb, steps = Toolbox(d, scores, use_llm=False), []
    disease = ds.CONDITIONS[pick_disease(question)]
    ranked = _record(tb, steps, "rank_counties", {"disease": disease}, on_step)
    if "error" not in ranked:
        county = ranked["counties"][0]["county"]
        det = _record(tb, steps, "county_details", {"county": county, "disease": disease}, on_step)
        if det.get("top_hospitals"):
            _record(tb, steps, "simulate_new_site", {
                "county": county, "hospital": det["top_hospitals"][0]["name"],
                "disease": disease}, on_step)
        _record(tb, steps, "write_outreach_flyer",
                {"county": county, "disease": disease, "language": "English"}, on_step)
    return {"steps": steps, "answer": template_answer(steps), "mode": "offline"}


def _assistant_msg(msg):
    out = {"role": "assistant", "content": msg.get("content") or ""}
    if msg.get("tool_calls"):
        out["tool_calls"] = msg["tool_calls"]
    return out


def run_scout(d, question, scores=None, chat=llm.chat_with_tools, on_step=None):
    """Returns {"steps": [...], "answer": str, "mode": "ai" | "offline"}.
    on_step(step) is called as each tool finishes; on_step(None) means AI failed and the
    run restarts in offline mode."""
    tb, steps = Toolbox(d, scores), []
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
    answer = None
    try:
        for _ in range(MAX_TOOL_CALLS + 3):  # hard bound on model turns
            msg = chat(messages, TOOLS if len(steps) < MAX_TOOL_CALLS else [])
            if not msg:
                raise RuntimeError("no reply from the model")
            calls = msg.get("tool_calls") or []
            if not calls:
                answer = (msg.get("content") or "").strip()
                if not answer:
                    raise RuntimeError("empty answer")
                break
            messages.append(_assistant_msg(msg))
            for call in calls:
                if len(steps) >= MAX_TOOL_CALLS:  # over the cap: tell the model, do not run
                    result = {"error": f"Tool call limit ({MAX_TOOL_CALLS}) reached. Give the final answer."}
                else:
                    fn = call["function"]
                    args = json.loads(fn.get("arguments") or "{}")
                    result = _record(tb, steps, fn["name"], args, on_step)
                messages.append({"role": "tool", "tool_call_id": call["id"],
                                 "content": json.dumps(result)})
        if answer is None:
            raise RuntimeError("model never gave a final answer")
    except Exception:
        if on_step:
            on_step(None)
        return fallback(d, question, scores, on_step)

    if not answer_is_safe(answer, steps, question):
        answer = template_answer(steps)
    return {"steps": steps, "answer": answer, "mode": "ai"}
