# Design: Site Scout

## Part A: simulate_new_site (deserts.py)

`county_scores` is split so the table can be rebuilt from any `sites` frame:

```
_score_table(d, mid, sites) -> (county_df, towns)     # old body of county_scores
county_scores(d, mid)       -> _score_table(d, mid, trial_sites(d, mid)) + sites
```

`simulate_new_site(d, mid, lat, lon, label)`:
1. `before, towns_b, sites = county_scores(d, mid)`.
2. Build one new row (nct `SIMULATED`, facility `label`, lat, lon). Its county is the county of the nearest
   town center, the same rule as `trial_sites`. Append it to `sites`.
3. `after, towns_a = _score_table(d, mid, sites_after)`.
4. `after["score"] = round(100 * ppt / before.people_per_trial.max())` (original max).
5. Add `rank` (1 = worst, by people_per_trial) to both. Add `newly_reached` = population of towns with
   `trials_in_reach == 0` before and `>= 1` after, summed per county (0 in before).

The new site is a new distinct trial, so `trials_in_reach` can only go up and `people_per_trial` can only go down.

## Part A: app.py County brief tab

Candidate hospital selectbox (hospitals with lat/lon), a button, and a result block in `st.session_state`
keyed by (county, disease, hospital): score before to after, rank change, residents newly within 25 miles.

## Part B: llm.chat_with_tools

POST to the Groq chat completions endpoint with `tools`, `tool_choice` auto, `reasoning_effort` low.
Returns `choices[0].message` (a dict) or `None`. Only the groq provider is supported; other providers return `None`.

## Part B: scout.py (no Streamlit imports)

```
TOOLS            OpenAI-style tool schemas
run_tool(d, name, args) -> JSON-safe dict       # dispatch; unknown name or bad args -> {"error": ...}
run_scout(d, question, chat=llm.chat_with_tools) -> {"steps": [...], "answer": str, "mode": "ai"|"offline"}
fallback(d, disease) -> same shape, mode "offline"
```

- Tools wrap `county_scores`, `candidate_hospitals`, `nearest_trials`, `ej_summary`, `simulate_new_site`
  and `llm.generate` (flyer; falls back to a rule-based flyer text).
- Step = `{"tool", "args", "summary", "result"}`; `summary` is a short one-line string.
- Loop: send messages and tools, run each requested tool call, append `role: tool` results, stop on a
  message with no tool calls or after 6 tool calls. Then one more call without tools for the final answer
  if needed.
- A system prompt requires: use only numbers from tool results, never say a person qualifies, mention
  ClinicalTrials.gov.
- `chat` is injectable so tests can pass a fake. Any failure (None, exception, bad JSON) switches to `fallback`.
- Disease is mapped from the question text (name match) and defaults to DIABETES.

## Part B: app.py Site Scout tab

Text input, three example buttons, `st.status` that lists steps as they run (run_scout takes an
`on_step` callback), then a bordered final card. Offline runs are labeled "offline mode".

## Testing

- P6 (Hypothesis): adding a site never increases any county's `people_per_trial`.
- Unit: fallback picks the worst county; every tool returns JSON-serializable data; fallback is used when
  `chat` returns None.
