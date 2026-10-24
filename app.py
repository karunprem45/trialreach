"""TrialReach: Streamlit UI only. All scoring lives in deserts.py."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

import deserts as ds
import llm

st.set_page_config(page_title="TrialReach", page_icon="🌵", layout="wide")

MODE_SCORE = "Research Desert Score (county)"
MODE_MILES = "Miles to nearest trial (town)"
LANGUAGES = ["English", "Spanish", "Portuguese", "Haitian Creole", "Chinese"]

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


def pretty(name):
    return str(name).title()


# ---------- cached data ----------
@st.cache_data
def get_data():
    return ds.load_all()


@st.cache_data
def get_scores(mid):
    return ds.county_scores(get_data(), mid)


try:
    d = get_data()
except FileNotFoundError:
    st.error("Data files are missing. Run `python fetch_data.py` once, then reload.")
    st.stop()

# ---------- sidebar ----------
with st.sidebar:
    st.title("🌵 TrialReach")
    mid = st.selectbox("Disease", list(ds.CONDITIONS), format_func=ds.CONDITIONS.get)
    mode = st.radio("Color the map by", [MODE_SCORE, MODE_MILES])
    show_sites = st.checkbox("Show trial sites", value=True)
    show_hosp = st.checkbox("Show acute hospitals", value=False)
    st.caption("The score is adults with the disease per recruiting trial within "
               f"{ds.REACH_MILES} miles. 100 is the county with the least research nearby.")

label = ds.CONDITIONS[mid]
counties, towns, sites = get_scores(mid)
worst = counties.iloc[0]

# ---------- A. header ----------
st.title("TrialReach")
st.subheader("Finding the research deserts of Massachusetts. "
             "Food deserts have a name. Research deserts don't.")

# ---------- B. metrics ----------
n_trials = sites["nct"].nunique()
n_boston = sites.loc[sites["county"] == "SUFFOLK", "nct"].nunique()
boston = counties[counties["county"] == "SUFFOLK"].iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Recruiting {label.lower()} trials in MA", f"{n_trials:,}")
c2.metric("Share with a Boston (Suffolk) site",
          f"{n_boston / n_trials:.0%}" if n_trials else "0%")
c3.metric("Worst research desert", pretty(worst["county"]),
          f"{worst['people_per_trial']:,.0f} people per nearby trial",
          delta_color="off", delta_arrow="off")
c4.metric("Gap vs. Boston", f"{worst['people_per_trial'] / boston['people_per_trial']:.0f}×",
          f"Boston: {boston['people_per_trial']:,.0f} per trial",
          delta_color="off", delta_arrow="off")

# ---------- C. map + ranking ----------
left, right = st.columns([3, 2])

with left:
    t = towns.copy()
    t["score"] = t["county"].map(counties.set_index("county")["score"])
    if mode == MODE_SCORE:
        z, zmin, zmax, bar = t["score"], 0, 100, "Score"
    else:
        z, zmin, zmax, bar = t["nearest_miles"], 0, float(np.percentile(t["nearest_miles"], 98)), "Miles"
    fig = go.Figure(go.Choroplethmap(
        geojson=d["shapes"], featureidkey="properties.TOWN20",
        locations=t["town"], z=z, zmin=zmin, zmax=zmax, colorscale="Reds",
        marker_line_color="white", marker_line_width=0.3,
        text=t["town"].map(pretty) + " (" + t["county"].map(pretty) + ")",
        hovertemplate="%{text}<br>" + bar + ": %{z:.0f}<extra></extra>",
        colorbar=dict(title=bar)))
    if show_sites and not sites.empty:
        s = sites.drop_duplicates(["facility", "lat", "lon"])
        fig.add_trace(go.Scattermap(
            lat=s["lat"], lon=s["lon"], mode="markers", marker=dict(size=7, color="royalblue"),
            text=s["facility"], hovertemplate="%{text}<extra>Trial site</extra>"))
    if show_hosp:
        h = d["hospitals"][d["hospitals"]["FACILITY_TYPE"] == "Acute Hospital"].dropna(subset=["lat", "lon"])
        fig.add_trace(go.Scattermap(
            lat=h["lat"], lon=h["lon"], mode="markers", marker=dict(size=8, color="green"),
            text=h["FACILITY_NAME"], hovertemplate="%{text}<extra>Acute hospital</extra>"))
    fig.update_layout(map_style="carto-positron", map_center=dict(lat=42.15, lon=-71.75),
                      map_zoom=6.9, height=560, margin=dict(l=0, r=0, t=0, b=0),
                      showlegend=False)
    st.plotly_chart(fig, config={"scrollZoom": False})

with right:
    st.markdown("**Counties, worst first**")
    rank = counties.assign(county=counties["county"].map(pretty))[
        ["county", "score", "people_per_trial", "prevalence", "trials_in_reach", "avg_miles"]]
    rank.columns = ["County", "Desert Score", "People per nearby trial", "% adults",
                    f"Trials ≤{ds.REACH_MILES} mi", "Miles to nearest"]
    st.dataframe(rank, hide_index=True, column_config={
        "Desert Score": st.column_config.ProgressColumn(
            "Desert Score", min_value=0, max_value=100, format="%d"),
        "People per nearby trial": st.column_config.NumberColumn(format="%d"),
        "% adults": st.column_config.NumberColumn(format="%.1f"),
        f"Trials ≤{ds.REACH_MILES} mi": st.column_config.NumberColumn(format="%.1f"),
        "Miles to nearest": st.column_config.NumberColumn(format="%.1f"),
    })

# ---------- D. county deep dive ----------
st.divider()
county = st.selectbox("Look closer at a county", list(counties["county"]),
                      format_func=pretty, key=f"county_{mid}")
row = counties[counties["county"] == county].iloc[0]
state_prev = ds.state_prevalence(counties)
hospitals = ds.candidate_hospitals(d, county, sites)
ej_pop, ej_towns = ds.ej_summary(d, county)
near = ds.nearest_trials(d, county, sites)
brief = ds.outreach_brief(label, row, state_prev, hospitals, ej_pop, ej_towns)

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("#### Recommendation")
    st.markdown(brief)
    st.caption(f"CDC 95% range for {label.lower()} in {pretty(county)}: "
               f"{row['prev_low']:.1f}% to {row['prev_high']:.1f}%")

    # AI brief (optional, with fallback)
    st.markdown("#### AI recruitment brief")
    lang = st.selectbox("Language", LANGUAGES)
    key = (county, mid, lang)
    if st.button("Write recruitment brief"):
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
            with st.spinner("Writing..."):
                st.session_state[key] = llm.generate("\n".join(facts), SYSTEM_PROMPT)
    if key in st.session_state:
        if st.session_state[key]:
            st.markdown(st.session_state[key])
        else:
            st.markdown(brief)
            st.caption("AI brief unavailable — showing the standard recommendation.")

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

    st.markdown("#### Where outreach has to try harder")
    if ej_towns.empty:
        st.info("No environmental-justice neighborhoods are listed in this county.")
    else:
        st.caption(f"About {ej_pop:,} residents live in environmental-justice neighborhoods.")
        et = ej_towns.head(10).assign(town=ej_towns.head(10)["town"].map(pretty))
        et.columns = ["Town", "EJ residents", "Neighborhoods", "Limited English (%)"]
        st.dataframe(et, hide_index=True, column_config={
            "Limited English (%)": st.column_config.NumberColumn(format="%.0f")})

# ---------- E. footer ----------
st.divider()
st.caption(
    "Sources: [ClinicalTrials.gov](https://clinicaltrials.gov) (U.S. NLM) · "
    "[CDC PLACES](https://www.cdc.gov/places) 2023 county crude prevalence · "
    "[MassGIS](https://www.mass.gov/orgs/massgis-bureau-of-geographic-information) "
    "(Census 2020 towns, hospitals, EJ 2020 block groups). "
    f"Data downloaded {d['fetched_at']}. "
    "TrialReach scores places, never people. Not medical advice. "
    "Distances are straight-line from town centers. Licensed beds are not live occupancy.")
