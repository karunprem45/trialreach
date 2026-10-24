"""Explore page: map, county brief and AI outreach. Display only."""
import html
import re

import numpy as np
import plotly.graph_objects as go
import streamlit as st

import deserts as ds
import llm
import ui
from ui import pretty

MODE_SCORE = "Research Desert Score (county)"
MODE_MILES = "Miles to nearest trial (town)"
LANGUAGES = ["English", "Spanish", "Portuguese", "Haitian Creole", "Chinese"]
SCORE_TITLE = "Research desert score (higher = fewer trials per person)"
MILES_TITLE = "Miles to nearest recruiting trial (higher = farther)"

SYSTEM_PROMPT = """You write short outreach text for a clinical research office in Massachusetts.
Rules:
- Use only the facts given. Do not invent numbers, trials or phone numbers.
- Never say the reader qualifies for a trial. Say "talk to your doctor or the study team".
- Mention that trial details are on ClinicalTrials.gov.
- Friendly, plain language. No medical advice.
Write exactly two parts:
## Resident flyer
At most 120 words, in the requested language, reading level about grade 6.
## Note for the hospital research office
Three short lines, in English."""


def story_line(label, counties, n_trials):
    """One sentence about the worst county vs. Boston (Suffolk)."""
    lc = label if label.isupper() else label.lower()  # keep "COPD"
    if n_trials == 0:
        return f"No recruiting {lc} trials with a Massachusetts site were found, so every county is a research desert."
    worst = counties.iloc[0]
    name = pretty(worst["county"])
    boston = counties[counties["county"] == "SUFFOLK"].iloc[0]
    ratio = worst["people_per_trial"] / boston["people_per_trial"] if boston["people_per_trial"] > 0 else 0
    if worst["county"] == "SUFFOLK" or ratio < 1.5:
        return (f"{name} is the biggest research desert for {lc}: "
                f"about {worst['people_per_trial']:,.0f} adults per nearby trial.")
    top_rate = counties.loc[counties["prevalence"].idxmax(), "county"] == worst["county"]
    lead = (f"{name} has the highest {lc} rate ({worst['prevalence']:.1f}% of adults)" if top_rate
            else f"{name} has {worst['prevalence']:.1f}% of adults with {lc}")
    return f"{lead} but about {ratio:.0f}x less research per person than Boston."


NOTE_HEAD = re.compile(r"^#+\s*note for the hospital.*$", re.I | re.M)
FLYER_HEAD = re.compile(r"^#+\s*resident flyer\s*$", re.I | re.M)


def split_brief(text):
    """Split the AI reply into (flyer, hospital note). Whole text is the flyer if no note heading."""
    m = NOTE_HEAD.search(text)
    flyer, note = (text[:m.start()], text[m.end():]) if m else (text, "")
    return FLYER_HEAD.sub("", flyer).strip(), note.strip()


def clicked_town(event, towns):
    """Town name from a map click, or None."""
    points = ((event or {}).get("selection") or {}).get("points") or []
    for p in points:
        if p.get("location"):
            return str(p["location"]).upper()
        if p.get("curve_number") == 0 and p.get("point_index") is not None:
            return towns["town"].iloc[p["point_index"]]
    return None


d = ui.load_data()

# ---------- hero ----------
st.title("Explore")
st.markdown("Pick a disease, click a town on the map and see where research is missing.")
mid = ui.disease_picker()
label = ds.CONDITIONS[mid]
counties, towns, sites = ui.get_scores(mid)
worst = counties.iloc[0]
boston = counties[counties["county"] == "SUFFOLK"].iloc[0]
n_trials = sites["nct"].nunique()
n_boston = sites.loc[sites["county"] == "SUFFOLK", "nct"].nunique()

st.markdown(f'<p class="lede">{html.escape(story_line(label, counties, n_trials))}</p>',
            unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Recruiting {ui.lower_label(label)} trials in MA", f"{n_trials:,}", border=True,
          help="Distinct studies on ClinicalTrials.gov that are recruiting and have at least "
               "one Massachusetts site.")
c2.metric("Share with a Boston (Suffolk) site",
          f"{n_boston / n_trials:.0%}" if n_trials else "0%", border=True,
          help="Share of those studies with a site in Suffolk County. A high share means "
               "research is concentrated in Boston.")
c3.metric("Worst research desert", pretty(worst["county"]),
          f"{worst['people_per_trial']:,.0f} people per nearby trial",
          delta_color="off", delta_arrow="off", border=True,
          help=f"The county with the most adults with {label.lower()} for each recruiting trial "
               f"within {ds.REACH_MILES} miles.")
c4.metric("Gap vs. Boston", f"{worst['people_per_trial'] / boston['people_per_trial']:.0f}×",
          f"Boston: {boston['people_per_trial']:,.0f} per trial",
          delta_color="off", delta_arrow="off", border=True,
          help="People per nearby trial in the worst county divided by the same number for Suffolk "
               "County (Boston).")

ui.data_caption(d)

# County picker. Created here so it sits above the tabs, filled after the map code
# runs so a map click can set st.session_state["county"] first.
picker = st.container()
names = list(counties["county"])
county_of = dict(zip(towns["town"], towns["county"]))

tab_map, tab_brief, tab_ai = st.tabs(["Map", "County brief", "AI outreach"])

# ---------- Map tab ----------
with tab_map:
    o1, o2 = st.columns([3, 2])
    mode = o1.radio("Color the map by", [MODE_SCORE, MODE_MILES], horizontal=True)
    show_sites = o2.checkbox("Show trial sites", value=True)
    show_hosp = o2.checkbox("Show acute hospitals", value=False)
    st.caption("The score is adults with the disease per recruiting trial within "
               f"{ds.REACH_MILES} miles. 100 is the county with the least research nearby.")
    if sites.empty:
        st.info(f"No recruiting {label.lower()} trials with a Massachusetts site were found. "
                "Every county shows as a research desert.")

    left, right = st.columns([3, 2])
    with left:
        cur = st.session_state.get("county")
        cur = cur if cur in names else names[0]
        t = towns.copy()
        t["score"] = t["county"].map(counties.set_index("county")["score"])
        if mode == MODE_SCORE:
            z, zmin, zmax, bar, bar_title = t["score"], 0, 100, "Score", SCORE_TITLE
        else:
            z, zmin, zmax, bar, bar_title = (t["nearest_miles"], 0,
                                             float(np.percentile(t["nearest_miles"], 98)),
                                             "Miles", MILES_TITLE)
        fig = go.Figure(go.Choroplethmap(
            geojson=d["shapes"], featureidkey="properties.TOWN20",
            locations=t["town"], z=z, zmin=zmin, zmax=zmax, colorscale="OrRd",
            marker_line_color="white", marker_line_width=0.3,
            text=t["town"].map(pretty) + " (" + t["county"].map(pretty) + ")",
            hovertemplate="%{text}<br>" + bar + ": %{z:.0f}<extra></extra>",
            showlegend=False,
            # keep full color after a click (no dimming of other towns)
            selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=1)),
            colorbar=dict(title=dict(text=bar_title, side="top"), orientation="h",
                          x=0.5, xanchor="center", y=-0.01, yanchor="top",
                          len=0.95, thickness=12)))
        # outline the selected county (only its shapes, to keep the figure small)
        keep = set(t.loc[t["county"] == cur, "town"])
        outline = {"type": "FeatureCollection", "features": [
            f for f in d["shapes"]["features"] if f["properties"]["TOWN20"].upper() in keep]}
        fig.add_trace(go.Choroplethmap(
            geojson=outline, featureidkey="properties.TOWN20",
            locations=sorted(keep), z=[0] * len(keep), showscale=False, showlegend=False,
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            marker_line_color="#222222", marker_line_width=1.6, hoverinfo="skip"))
        if show_sites and not sites.empty:
            s = sites.drop_duplicates(["facility", "lat", "lon"])
            fig.add_trace(go.Scattermap(
                lat=s["lat"], lon=s["lon"], mode="markers", name="Trial site",
                marker=dict(size=7, color="#1F5FBF"),
                text=s["facility"], hovertemplate="%{text}<extra>Trial site</extra>"))
        if show_hosp:
            h = d["hospitals"][d["hospitals"]["FACILITY_TYPE"] == "Acute Hospital"].dropna(subset=["lat", "lon"])
            fig.add_trace(go.Scattermap(
                lat=h["lat"], lon=h["lon"], mode="markers", name="Acute hospital",
                marker=dict(size=8, color="#222222"),
                text=h["FACILITY_NAME"], hovertemplate="%{text}<extra>Acute hospital</extra>"))
        fig.update_layout(
            map_style="carto-positron", map_center=dict(lat=42.15, lon=-71.75), map_zoom=6.9,
            height=520, margin=dict(l=0, r=0, t=0, b=80), showlegend=True,
            legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,250,243,0.9)", itemclick=False,
                        itemdoubleclick=False))
        event = st.plotly_chart(fig, key=f"map_{mid}", on_select="rerun",
                                selection_mode="points", config={"scrollZoom": False})

        # A new click selects that town's county (seen_town ignores a stale selection).
        town = clicked_town(event, t)
        if town != st.session_state.get("seen_town"):
            st.session_state["seen_town"] = town
            hit = county_of.get(town)
            if hit and hit != st.session_state.get("county"):
                st.session_state["county"] = hit
                st.rerun()
        st.caption(f"Selected: {pretty(cur)} County. Click a town to change it, or use the "
                   "county picker above the tabs. Open the County brief tab for details.")

    with right:
        st.markdown("**Counties, worst first**")
        rank = counties.assign(county=counties["county"].map(pretty))[
            ["county", "score", "people_per_trial", "prevalence", "trials_in_reach", "avg_miles"]]
        rank.columns = ["County", "Desert Score", "People per nearby trial", "Share of adults (%)",
                        f"Trials ≤{ds.REACH_MILES} mi", "Miles to nearest"]
        st.dataframe(rank, hide_index=True, column_config={
            "Desert Score": st.column_config.ProgressColumn(
                "Desert Score", min_value=0, max_value=100, format="%d"),
            "People per nearby trial": st.column_config.NumberColumn(format="%d"),
            "Share of adults (%)": st.column_config.NumberColumn(
                format="%.1f", help="Share of adults with the disease (CDC PLACES)."),
            f"Trials ≤{ds.REACH_MILES} mi": st.column_config.NumberColumn(format="%.1f"),
            "Miles to nearest": st.column_config.NumberColumn(format="%.1f"),
        })

# ---------- county picker (fallback for the map click) ----------
with picker:
    county = st.selectbox("Selected county (click a town on the map, or choose here)",
                          names, format_func=pretty, key="county")

row = counties[counties["county"] == county].iloc[0]
state_prev = ds.state_prevalence(counties)
hospitals = ds.candidate_hospitals(d, county, sites)
ej_pop, ej_towns = ds.ej_summary(d, county)
near = ds.nearest_trials(d, county, sites)
brief = ds.outreach_brief(label, row, state_prev, hospitals, ej_pop, ej_towns)
brief_plain = ui.plain(brief)

# ---------- County brief tab ----------
with tab_brief:
    st.markdown(f"### {pretty(county)} County · {label}")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Recommendation")
        st.markdown(brief_plain)
        st.caption(f"CDC 95% range for the share of adults with {label.lower()} in {pretty(county)}: "
                   f"{row['prev_low']:.1f}% to {row['prev_high']:.1f}%")

        st.markdown("#### Nearest recruiting trials")
        if near.empty:
            st.info("No recruiting trials were found for this disease.")
        else:
            tbl = near.assign(link="https://clinicaltrials.gov/study/" + near["nct"])
            tbl = tbl[["miles", "title", "phase", "city", "link"]]
            tbl.columns = ["Miles", "Study", "Phase", "Site city", "Record"]
            st.dataframe(tbl, hide_index=True, column_config={
                "Miles": st.column_config.NumberColumn(format="%.1f"),
                "Record": st.column_config.LinkColumn("Record", display_text="Open")})

    with col_b:
        st.markdown("#### Hospitals that could host a study")
        if hospitals.empty:
            st.info("No acute hospitals are listed in this county. Look at partners nearby.")
        else:
            ht = hospitals.assign(town=hospitals["MUNICIPALITY"].map(pretty))[
                ["FACILITY_NAME", "town", "beds", "ICU", "nearest_trial_miles"]]
            ht.columns = ["Hospital", "Town", "Licensed beds", "ICU beds", "Miles to nearest trial"]
            st.dataframe(ht, hide_index=True, column_config={
                "Miles to nearest trial": st.column_config.NumberColumn(format="%.1f")})

        st.markdown("#### Neighborhoods that need extra outreach")
        if ej_towns.empty:
            st.info("No neighborhoods that need extra outreach are listed in this county.")
        else:
            st.caption(f"About {ej_pop:,} residents live in neighborhoods that need extra outreach.",
                       help="MassGIS environmental-justice neighborhoods (2020): areas with higher "
                            "shares of low-income, minority or limited-English households.")
            et = ej_towns.head(10).assign(town=ej_towns.head(10)["town"].map(pretty))
            et.columns = ["Town", "Residents", "Neighborhoods", "Limited English (%)"]
            st.dataframe(et, hide_index=True, column_config={
                "Limited English (%)": st.column_config.NumberColumn(format="%.0f")})

    # What-if simulator: add one hypothetical trial site at a candidate hospital
    st.markdown("#### What if a hospital opened a study?")
    cands = hospitals.dropna(subset=["lat", "lon"])
    if cands.empty:
        st.info("No acute hospital with a map location is listed in this county.")
    else:
        hname = st.selectbox("Candidate hospital", list(cands["FACILITY_NAME"]), key="sim_hospital")
        sim_key = (county, mid, hname)
        if st.button("Simulate a new trial site here"):
            h = cands[cands["FACILITY_NAME"] == hname].iloc[0]
            st.session_state["sim"] = (sim_key, ds.simulate_new_site(
                d, mid, float(h["lat"]), float(h["lon"]), hname))
        sim = st.session_state.get("sim")
        if sim and sim[0] == sim_key:
            b = sim[1][0].set_index("county").loc[county]
            a = sim[1][1].set_index("county").loc[county]
            moved = int(a["rank"] - b["rank"])
            r1, r2, r3 = st.columns(3)
            r1.metric("Desert score", f"{int(a['score'])}", f"{int(a['score'] - b['score'])} from {int(b['score'])}",
                      delta_color="inverse", border=True,
                      help="100 is the worst county today. After scaling uses today's worst county, so the two are comparable.")
            r2.metric("Rank (1 = worst)", f"{int(a['rank'])}",
                      f"{moved:+d} from {int(b['rank'])}" if moved else f"no change from {int(b['rank'])}",
                      delta_color="off", border=True)
            r3.metric(f"Residents newly within {ds.REACH_MILES} mi of a trial",
                      f"{int(sim[1][1]['newly_reached'].sum()):,}", border=True,
                      help="Residents in towns that had no recruiting trial within reach before.")
            st.caption("This is a what-if on public place-level data, not a plan or a promise of a study. "
                       "The new site counts as one added trial.")

# ---------- AI outreach tab ----------
with tab_ai:
    st.markdown(f"### Outreach for {pretty(county)} County · {label}")
    lang = st.selectbox("Language", LANGUAGES)
    key = (county, mid, lang)
    if st.button("Write recruitment brief", type="primary"):
        if key not in st.session_state:
            top = hospitals.iloc[0] if len(hospitals) else None
            lep = ej_towns.sort_values("limited_english_pct", ascending=False).iloc[0] if len(ej_towns) else None
            facts = [
                f"County: {pretty(county)}", f"Disease: {label}",
                f"Prevalence: {row['prevalence']:.1f}% of adults (state average {state_prev:.1f}%)",
                f"People per nearby trial: {row['people_per_trial']:,.0f}",
                f"Trials within {ds.REACH_MILES} miles: {row['trials_in_reach']:.1f} on average",
                "Top hospital: " + (f"{top['FACILITY_NAME']} in {pretty(top['MUNICIPALITY'])}" if top is not None else "none listed"),
                "Nearest trials: " + ("; ".join(f"{r.title} ({r.nct})" for r in near.head(3).itertuples()) or "none"),
                "Town with most limited-English households: " + (f"{pretty(lep['town'])} ({lep['limited_english_pct']:.0f}%)" if lep is not None else "none"),
                f"Language for the flyer: {lang}",
            ]
            with st.spinner("Writing the brief. This can take up to 20 seconds..."):
                st.session_state[key] = llm.generate("\n".join(facts), SYSTEM_PROMPT)

    if key not in st.session_state:
        st.info("Pick a language and press the button. TrialReach drafts a short flyer for "
                "residents and a note for the hospital research office. Review the text before "
                "you share it.")
    else:
        text = st.session_state[key]
        ai_ok = bool(text)
        flyer, note = split_brief(text) if ai_ok else (brief_plain, "")
        if not ai_ok:
            st.info("The AI brief is unavailable right now. Showing the standard recommendation.")

        with st.container(border=True):
            st.markdown("#### Resident flyer" if ai_ok else "#### Standard recommendation")
            st.markdown(flyer)

        footer = "Trial details are on ClinicalTrials.gov. Not medical advice. Talk to your doctor or the study team."
        if ai_ok:
            footer += " Drafted with an AI tool; review before sharing."
        doc = f"# {pretty(county)} County · {label} ({lang})\n\n{flyer}\n\n---\n_{footer}_\n"
        fname = re.sub(r"[^a-z0-9]+", "-", f"trialreach-{county}-{mid}-{lang}".lower()).strip("-") + ".md"
        st.download_button("Download as Markdown", data=doc, file_name=fname,
                           mime="text/markdown", on_click="ignore", key=f"dl_{fname}")

        if note:
            st.markdown("#### Note for the hospital research office")
            st.markdown(note)
