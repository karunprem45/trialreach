"""Story page: five short sections. Display only; numbers come from deserts.py."""
import plotly.graph_objects as go
import streamlit as st

import deserts as ds
import ui
from ui import em, esc

MIN_EJ_RESIDENTS = 1000  # towns with fewer residents in these neighborhoods are skipped


def head(num, headline, sentence):
    """Small number, big headline (already-escaped HTML) and one short sentence."""
    st.markdown(f'<p class="num">{num}</p><h2 class="headline">{headline}</h2>'
                f'<p class="lede">{esc(sentence)}</p>', unsafe_allow_html=True)


def trials_word(n):
    return "trial" if n == 1 else "trials"


d = ui.load_data()
with st.container(key="story-0"):
    mid = ui.disease_picker()
label = ds.CONDITIONS[mid]
lc = ui.lower_label(label)
counties, towns, sites = ui.get_scores(mid)
worst = counties.iloc[0]
w_name = ui.county_label(worst["county"])
n_trials = sites["nct"].nunique()

# ---------- 01 Most trials are in Boston ----------
with st.container(key="story-1"):
    if n_trials == 0:
        head("01", f"No recruiting {esc(lc)} trials with a Massachusetts site were found.",
             "Every county is a research desert for this disease.")
    else:
        n_boston = sites.loc[sites["county"] == ui.BOSTON, "nct"].nunique()
        share = n_boston / n_trials
        title = ("Most clinical trials in Massachusetts are in " + em("Boston") + "."
                 if share >= 0.5 else
                 "Only " + em(f"{share:.0%}") + " of clinical trials in Massachusetts are in Boston.")
        head("01", title,
             f"{n_boston} of the {n_trials} recruiting {lc} {trials_word(n_trials)} ({share:.0%}) "
             "have a site in Boston.")
        pts = sites.drop_duplicates(["facility", "lat", "lon"])
        fig = go.Figure()
        for name, mask, color, size in (
                ("Rest of Massachusetts", pts["county"] != ui.BOSTON, ui.TEXT, 7),
                ("Boston", pts["county"] == ui.BOSTON, ui.ACCENT, 8)):
            p = pts[mask]
            fig.add_trace(go.Scattermap(
                lat=p["lat"], lon=p["lon"], mode="markers", name=name,
                marker=dict(size=size, color=color, opacity=0.8),
                text=p["facility"], hovertemplate="%{text}<extra>" + name + "</extra>"))
        fig.update_layout(
            map_style="carto-darkmatter", map_center=dict(lat=42.2, lon=-71.8), map_zoom=6.6,
            height=380, margin=dict(l=0, r=0, t=0, b=0), showlegend=True,
            font=dict(color=ui.TEXT), paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(x=0.01, y=0.99, bgcolor="rgba(23,23,26,0.9)", itemclick=False,
                        itemdoubleclick=False))
        st.plotly_chart(fig, key=f"story_map_{mid}", config={"scrollZoom": False, "displayModeBar": False})
        st.caption("Source: ClinicalTrials.gov, recruiting studies with a Massachusetts site.",
                   help=ui.BOSTON_NOTE + " A study counts once, even if it has several sites.")

# ---------- 02 Few trials per person outside Boston ----------
with st.container(key="story-2"):
    other = (counties[counties["county"] == ui.BOSTON].iloc[0]
             if worst["county"] != ui.BOSTON else counties.iloc[1])
    o_name = ui.county_label(other["county"])
    n_worst, n_other = worst["people_per_trial"], other["people_per_trial"]
    head("02",
         f"In {em(w_name)}, {em(f'{n_worst:,.0f}')} people with {esc(lc)} share one nearby trial. "
         f"In {em(o_name)}, it's {em(f'{n_other:,.0f}')}.",
         (f"That is about {n_worst / n_other:,.0f} times as many people per trial."
          if n_other > 0 and n_worst / n_other >= 1.5 else
          "The gap is small for this disease."))
    bar = go.Figure(go.Bar(
        y=[w_name, o_name], x=[n_worst, n_other], orientation="h",
        marker_color=[ui.ACCENT, ui.BAR_GRAY], width=0.55,
        text=[f"{n_worst:,.0f}", f"{n_other:,.0f}"], textposition="outside", cliponaxis=False,
        textfont=dict(size=16, color=ui.TEXT), hoverinfo="skip"))
    bar.update_layout(
        height=190, margin=dict(l=0, r=30, t=0, b=0), showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=ui.TEXT, size=15),
        xaxis=dict(visible=False, showgrid=False, zeroline=False, range=[0, max(n_worst, 1) * 1.2]),
        yaxis=dict(showgrid=False, zeroline=False, autorange="reversed", ticks="",
                   automargin=True))  # grow the left margin to fit full county names
    st.plotly_chart(bar, key=f"story_bar_{mid}", config={"staticPlot": True})
    st.caption("People with the disease for each nearby recruiting trial.",
               help=f"Estimated adults with the disease (CDC PLACES share of adults times county "
                    f"population) divided by the average number of recruiting trials within "
                    f"{ds.REACH_MILES} miles, plus one. {ui.BOSTON_NOTE}")

# ---------- 03 Limited English ----------
with st.container(key="story-3"):
    _, ej_towns = ds.ej_summary(d, worst["county"])
    pool = ej_towns[ej_towns["ej_pop"] >= MIN_EJ_RESIDENTS]
    pool = pool if len(pool) else ej_towns
    top3 = pool.sort_values("limited_english_pct", ascending=False).head(3)
    top3 = top3[top3["limited_english_pct"] >= 1]  # also avoids dividing by zero below
    if top3.empty:
        head("03", "Some neighborhoods need extra outreach.",
             f"No neighborhoods that need extra outreach are listed in {w_name}.")
    else:
        rows = [(ui.pretty(r.town), max(1, round(100 / r.limited_english_pct)), r.ej_pop)
                for r in top3.itertuples()]
        town, x, _ = rows[0]
        head("03", f"In {em(town)}, 1 in {em(x)} homes has limited English.",
             f"These are neighborhoods that need extra outreach in {w_name}, "
             f"the biggest gap for {lc}.")
        st.markdown(ui.cards([(f"1 in {x}", t, f"homes with limited English · about {pop:,} "
                               "residents in these neighborhoods") for t, x, pop in rows]),
                    unsafe_allow_html=True)
        st.caption("Source: MassGIS 2020.",
                   help="Share of homes with limited English in neighborhoods that need extra "
                        "outreach (MassGIS environmental-justice areas). Towns need at least "
                        f"{MIN_EJ_RESIDENTS:,} residents in these neighborhoods to be listed.")

# ---------- 04 One new site ----------
with st.container(key="story-4"):
    cands = ds.candidate_hospitals(d, worst["county"], sites).dropna(subset=["lat", "lon"])
    if cands.empty:
        head("04", "A new trial site needs a hospital partner.",
             f"No acute hospital with a map location is listed in {w_name}. Look at partners nearby.")
    else:
        hosp = cands.iloc[0]
        before, after = ui.get_sim(mid, float(hosp["lat"]), float(hosp["lon"]), hosp["FACILITY_NAME"])
        k = int(after["newly_reached"].sum())
        b = float(before.set_index("county").loc[worst["county"], "people_per_trial"])
        a = float(after.set_index("county").loc[worst["county"], "people_per_trial"])
        h_name = hosp["FACILITY_NAME"]
        if k > 0:
            head("04", f"One new trial site at {em(h_name)} would bring {em(f'{k:,}')} more "
                 "residents within reach.",
                 f"Within reach means within {ds.REACH_MILES} miles of a recruiting {lc} trial. "
                 "This is a what-if, not a plan.")
        else:
            head("04", f"One new trial site at {em(h_name)} would cut the people per trial in "
                 f"{esc(w_name)} from {em(f'{b:,.0f}')} to {em(f'{a:,.0f}')}.",
                 "Nearby residents already have a trial within reach, so the gain is fewer people "
                 "per trial. This is a what-if, not a plan.")
        st.markdown(ui.cards([
            (f"{b:,.0f}", "Today", f"people per nearby trial in {w_name}"),
            (f"{a:,.0f}", "With one new site", f"people per nearby trial in {w_name}"),
            (f"{k:,}", "More residents in reach", f"within {ds.REACH_MILES} miles of a trial")]),
            unsafe_allow_html=True)
        st.caption(f"What-if at {h_name}, the acute hospital with the most licensed beds in {w_name}.",
                   help="Adds one pretend trial site at the hospital and re-runs the same score. "
                        "It is based on public place-level data and does not promise a study.")

# ---------- 05 Next steps ----------
with st.container(key="story-5"):
    head("05", "See the full picture.",
         "Explore every county on the map, or ask Site Scout where the next site should go.")
    b1, b2 = st.columns(2)
    with b1, st.container(key="cta-primary"):
        st.page_link("page_explore.py", label="Explore the map", width="stretch")
    with b2, st.container(key="cta-secondary"):
        st.page_link("page_scout.py", label="Ask Site Scout", width="stretch")
    ui.data_caption(d)
