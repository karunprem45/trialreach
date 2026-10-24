# 04 · UI Specification (app.py, Streamlit)

`st.set_page_config(page_title="TrialReach", page_icon="🌵", layout="wide")`

## Sidebar
1. Title "🌵 TrialReach"
2. Selectbox **Disease** (9 labels)
3. Radio **Color the map by**: "Research Desert Score (county)" / "Miles to nearest trial (town)"
4. Checkbox **Show trial sites** (default on), **Show acute hospitals** (default off)
5. Caption explaining the score in one sentence

## Main page, top to bottom
**A. Header.** Title "TrialReach", subtitle: "Finding the research deserts of Massachusetts. Food deserts have a name. Research deserts don't."

**B. 4 metrics (st.columns(4))**
| Metric | Value | Small text under it |
|---|---|---|
| Recruiting {disease} trials in MA | distinct NCT count | – |
| Share with a Boston (Suffolk) site | % | – |
| Worst research desert | county name | "{people_per_trial:,} people per nearby trial" |
| Gap vs. Boston | worst ÷ Suffolk people_per_trial, e.g. "21×" | "Boston: 861 per trial" |
Use `delta_color="off", delta_arrow="off"` for the small text so no arrows show.

**C. Map (left, 3/5 width) + Ranking (right, 2/5 width)**
- Map: `go.Choroplethmap` on towns.geojson, `featureidkey="properties.TOWN20"`, colorscale "Reds", white 0.3 px borders.
  Score mode: each town colored by its county score (0–100). Miles mode: town nearest_miles, zmax = 98th percentile.
  Trial sites: `go.Scattermap` blue dots (dedupe by facility+lat+lon). Hospitals: green dots.
  `map_style="carto-positron"`, center (42.15, -71.75), zoom 6.9, height 560.
  `st.plotly_chart(fig, config={"scrollZoom": False})` so page scrolling works during the demo.
- Ranking: `st.dataframe` with columns County, Desert Score (ProgressColumn 0–100), People per nearby trial
  (format "localized"), % adults, Trials ≤25 mi, Miles to nearest.

**D. County deep dive** (selectbox "Look closer at a county", default = worst)
- Left column: "Recommendation" (outreach_brief markdown) + CDC 95% range caption;
  then **AI brief** controls (docs/05); then "Nearest recruiting trials" table: Miles, Study, Phase, Site city,
  Record (LinkColumn to `https://clinicaltrials.gov/study/{nct}`, display "Open"), 8 rows, measured from the
  county's population-weighted center.
- Right column: "Hospitals that could host a study" (Hospital, Town, Licensed beds, ICU beds, Miles to nearest trial)
  and "Where outreach has to try harder" (EJ table, top 10 towns).
- Empty states: show `st.info` with a friendly sentence, never an error.

**E. Footer** caption: data sources with links + "TrialReach scores places, never people. Not medical advice.
Distances are straight-line from town centers. Licensed beds are not live occupancy."

Title-case all UPPERCASE names before display.
