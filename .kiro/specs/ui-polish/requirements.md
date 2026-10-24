# Requirements: UI Polish

## Introduction

Polish the Streamlit UI so judges see a clear story, an accessible layout and a usable map on any screen size. Scope is `app.py` and `.streamlit/config.toml` only. `deserts.py`, `llm.py` and `fetch_data.py` do not change.

## Requirements

### 1. Hero
**User story:** As a judge, I want the problem and the finding in the first screen.
1.1 The page shows the title, the disease selector and one live sentence for the selected disease, built from the worst county and the Boston (Suffolk) gap, for example "Hampden has the highest diabetes rate but about 21x less research per person than Boston."
1.2 Four stat cards (bordered) each have a `help` tooltip: recruiting trials, share with a Boston site, worst research desert, gap vs. Boston.
1.3 Under the hero, a small caption reads "Data updated <date> · Sources" with links to ClinicalTrials.gov, CDC PLACES and MassGIS.
1.4 The sentence handles edge cases (no trials, worst county is Suffolk) without errors.

### 2. Tabs
2.1 `st.tabs` with "Map", "County brief", "AI outreach".
2.2 Map tab: map controls, map, county ranking table.
2.3 County brief tab: recommendation, nearest trials, hospitals, EJ table.
2.4 AI outreach tab: language select, generate button, flyer in a bordered card, `st.download_button` (markdown) and the hospital note.

### 3. Map click
3.1 Clicking a town selects its county via `st.plotly_chart(on_select=...)`.
3.2 The county selectbox stays as the fallback (keyboard and screen reader users) and always shows the current county.
3.3 The selected county is outlined on the map and named under it.

### 4. Theme and map
4.1 `.streamlit/config.toml`: base light, primaryColor `#C2502E`, backgroundColor `#FFFAF3`, secondaryBackgroundColor `#F3E9DC`, font "sans serif".
4.2 Map colorscale `OrRd`; colorbar title "Research desert score (higher = fewer trials per person)" in score mode.
4.3 Trial sites and hospitals have distinct colors and a legend.

### 5. Feedback states
5.1 `st.spinner` while the AI brief is written.
5.2 Friendly `st.info` empty states: no trials, no hospitals, no EJ towns, no brief yet.
5.3 If the AI brief is unavailable, show the standard recommendation with a note (existing fallback).

### 6. Small screens
6.1 No sidebar. All controls are in the main column so they are reachable on a phone.
6.2 Columns stack on narrow screens; light CSS trims page padding and font sizes under 640 px.
6.3 Tables scroll inside their own container.

### 7. Safety and sources (unchanged)
7.1 Keep the footer: sources, "scores places, never people", "Not medical advice", straight-line distances, licensed beds are not live occupancy.
7.2 The flyer download ends with a source and "not medical advice" line.
7.3 The system prompt and `llm.generate` call are unchanged.
