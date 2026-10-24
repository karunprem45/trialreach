# Design: Story Page

## Files (flat, as in the structure rule)

```
app.py           router: page config, CSS, brand header, st.navigation(position="top"), footer
ui.py            shared UI helpers: pretty, plain, cached data, disease picker, CSS, footer, cards
page_story.py    Story page (5 sections)
page_explore.py  the old Map / County brief / AI outreach tabs
page_scout.py    the old Site Scout tab
.streamlit/config.toml   colors + Google Fonts (Inter text, serif headings)
```

`deserts.py`, `llm.py`, `scout.py` are not touched. Page files are not in a folder named `pages/` so Streamlit's old auto-routing stays off.

## Navigation

`st.navigation([Page("page_story.py", default=True), Page("page_explore.py"), Page("page_scout.py")], position="top")`, then `pg.run()`, then the footer. Code after `pg.run()` runs on every page.

## Shared disease

Widget keys are dropped when a page stops rendering them. So the choice lives in `st.session_state["mid"]` (plain value). `ui.disease_picker()` shows a selectbox whose `index` comes from that value and writes the new value back.

## Story data (all from existing functions)

| Section | Source |
|---|---|
| 01 | `county_scores` -> `sites`. Boston share = distinct NCT ids with a Suffolk site / all NCT ids. Map = `sites` deduplicated by (facility, lat, lon). |
| 02 | `counties.iloc[0]` (worst) vs Suffolk row. Uses `people_per_trial`. If worst is Suffolk, compare with the second worst. |
| 03 | `ds.ej_summary(d, worst)`, sorted by `limited_english_pct`, keep `ej_pop >= 1000`, top 3. X = `round(100 / pct)`. |
| 04 | `ds.candidate_hospitals(d, worst, sites)` -> first row with lat/lon -> `ds.simulate_new_site`. K = `after["newly_reached"].sum()`. Before/after = worst county `people_per_trial`. Cached with `st.cache_data`. |
| 05 | `st.page_link("page_explore.py")`, `st.page_link("page_scout.py")`. |

## Layout and motion

- Each section is `st.container(key="story-N")`, which adds the CSS class `st-key-story-N`. CSS fades it in with `@keyframes` and a small stagger. `@media (prefers-reduced-motion: reduce)` sets `animation: none`.
- Headline = `<h2>` with the serif font and `clamp(1.7rem, 5vw, 2.6rem)`. Key numbers in `<em>` colored with the accent (not italic).
- `.cards` is a CSS grid, `repeat(auto-fit, minmax(220px, 1fr))`, so cards wrap into one column on phones. Card background `#F3E9DC`.
- Page links styled as buttons with CSS on `[data-testid="stPageLink"] a`.
- All dynamic text is passed through `html.escape` before it goes into HTML.

## Charts

- Section 02: horizontal `go.Bar`, 2 bars, gray `#CFC6BD`, worst county `#C2502E`, `text` = value, `textposition="outside"`, hidden x axis, no grid, transparent background.
- Section 01: `go.Scattermap`, `carto-positron`, Boston dots accent, other dots gray, zoom 6.9.

## Plain words

`ui.plain(text)` replaces "environmental-justice neighborhoods" with "neighborhoods that need extra outreach" and "prevalence" with "share of adults". Used on text from `deserts.outreach_brief` and `scout` answers. Column titles on the Explore page are renamed directly.

## Not changing

`deserts.py`, `llm.py`, `scout.py`, `fetch_data.py`, tests, `SYSTEM_PROMPT`, the Explore map and click logic.

## Verification

`pytest -q`, then an `AppTest` run of all three pages (default and a second disease). Visual checks (fonts, fade-in, phone layout) cannot run in AppTest and are left for the user in a browser.
