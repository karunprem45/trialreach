# Requirements: Story Page

## Introduction

Add a simple Story page that a non-technical judge understands in seconds, and split the app into three pages with `st.navigation`. Scope is UI only: `app.py`, new page files, `.streamlit/config.toml`. `deserts.py`, `llm.py` and `scout.py` logic do not change. No emojis anywhere (titles, page icon, labels, buttons).

## Requirements

### 1. Pages
**User story:** As a judge, I want to land on the story and open the details when I want them.
1.1 `st.navigation` with three pages: "Story" (default), "Explore" (the current Map, County brief and AI outreach tabs), "Site Scout" (the current Site Scout tab).
1.2 The selected disease (default Diabetes) is remembered when the user moves between pages.
1.3 Brand name and page links are visible at the top of every page.

### 2. Story page: five sections
Each section has a small number label ("01"), one big headline with real numbers for the selected disease, one short sentence and one simple visual.
2.1 Section 01: "Most clinical trials in Massachusetts are in Boston." Visual: map of trial dots (Boston dots in the accent color, others gray). Sentence gives the share of trials with a Boston site. If the share is under 50%, the headline states the share instead of "Most".
2.2 Section 02: "In <worst county>, <N> people with <disease> share one nearby trial. In Boston, it's <M>." Visual: 2-bar chart with labels on the bars.
2.3 Section 03: "In <top town>, 1 in <X> homes has limited English." Visual: list of the top 3 towns. Towns come from the worst county of section 02 (the place to reach first) and need at least 1,000 residents in the neighborhoods counted, so tiny areas do not win.
2.4 Section 04: "One new trial site at <top hospital> would bring <K> more residents within reach." Visual: before and after numbers from `simulate_new_site`. The top hospital is the acute hospital with the most licensed beds in the worst county. If K is 0, the headline uses the before and after people-per-trial instead.
2.5 Section 05: two buttons, "Explore the map" and "Ask Site Scout", made with `st.page_link`.
2.6 Edge cases (no trials, worst county is Suffolk, no neighborhoods listed, no hospital with a location) show a short plain message and never raise.

### 3. Plain words
3.1 On screen: "neighborhoods that need extra outreach" instead of "environmental-justice block groups"; "share of adults" instead of "prevalence".
3.2 Short tooltips (`help=`) carry the details (Boston means Suffolk County, how people per trial is counted, what "within reach" means).
3.3 Text produced by `deserts.py` and `scout.py` is passed through a display-only word swap; their logic is untouched.

### 4. Look
4.1 Fonts from Google Fonts: a serif for headlines, Inter for text.
4.2 Colors: ink `#1F1A17`, muted `#6B625C`, background `#FFFAF3`, card `#F3E9DC`, accent `#C2502E`.
4.3 Lots of white space. Page max width 1000 px.
4.4 Each story section fades in gently (CSS only). The animation is off under `prefers-reduced-motion: reduce`.

### 5. Charts
5.1 Clean Plotly: no gridlines, labels on the bars, no axis clutter.
5.2 Bars are gray; only the highlighted county uses the accent color.
5.3 Maps use `go.Scattermap` / `go.Choroplethmap` with `carto-positron`.

### 6. Small screens
6.1 Sections stack on phones: cards use a CSS grid that wraps, buttons stack.
6.2 Headline sizes scale down with `clamp()`.

### 7. Safety and sources (unchanged)
7.1 Keep the footer on every page: sources, "scores places, never people", "Not medical advice", straight-line distances, licensed beds are not live occupancy.
7.2 The Story page also shows a "Data updated" caption with source links.
7.3 Never say a person qualifies for a trial. No personal health data.
7.4 `SYSTEM_PROMPT`, `llm.generate` and `scout.run_scout` calls are unchanged.

### 8. Verification
8.1 `pytest -q` passes.
8.2 An `AppTest` smoke run loads all three pages without exceptions (not committed).
