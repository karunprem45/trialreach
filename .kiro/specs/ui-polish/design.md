# Design: UI Polish

## Page flow (app.py)

```
title + tagline
disease selectbox
story sentence            (hero)
4 stat cards              (st.metric border=True + help)
caption: Data updated · Sources
county picker container   (filled later, so a map click can set it first)
tabs: Map | County brief | AI outreach
footer (unchanged safety text)
```

## Map click -> county

- `st.plotly_chart(fig, key=f"map_{mid}", on_select="rerun", selection_mode="points")` returns the selection.
- `clicked_town(event)` reads the first point with a `location` (fallback: `point_index` on trace 0) and returns the town name or None.
- `st.session_state["county"]` is the single source of truth and is the key of the picker selectbox.
- `seen_town` in session state remembers the last handled click, so a stale selection never overrides the selectbox.
- On a new click: set `county`, then `st.rerun()` so the outline and picker agree. The picker container is created above the tabs but filled after the map code runs. This avoids setting a widget's state after it exists.
- Highlight: a second `Choroplethmap` with a transparent fill and a dark outline, using only the selected county's GeoJSON features (keeps the payload small), `hoverinfo="skip"` so clicks reach the base trace. Base trace `selected/unselected` opacity is 1 so a click does not dim the map.

## Hero story

Pure display logic in `app.py` (`story_line`): worst county vs Boston from `counties`. Uses "the highest {disease} rate" only when the worst county also has the highest prevalence. Falls back to a "{ppt} adults per nearby trial" sentence if the worst county is Suffolk or there are no trials.

## AI outreach

- Same cache key `(county, mid, lang)` in `st.session_state`, same prompt and `llm.generate` call.
- `split_brief(text)` splits the reply at the "Note for the hospital research office" heading into flyer and note (whole text is the flyer if the heading is missing).
- Flyer in `st.container(border=True)`. `st.download_button(..., on_click="ignore")` saves flyer + source line as `.md`.
- Fallback: standard recommendation in the card, caption "AI brief unavailable", download still works.

## Theme and CSS

- `.streamlit/config.toml` holds the four colors and font.
- One small `<style>` block: page padding, stat card radius, `.story` callout, `@media (max-width: 640px)` tweaks. Contrast: `#C2502E` on `#FFFAF3` is about 4.5:1; button text is white on `#C2502E` (about 4.7:1).

## Map

- Score mode: `OrRd`, 0 to 100, horizontal colorbar under the map with the long title. Miles mode: `OrRd`, title "Miles to nearest recruiting trial (higher = farther)".
- Trial sites blue `#1F5FBF`, hospitals dark `#222222`, legend top-left.
- Map height 520.

## Not changing

`deserts.py`, `llm.py`, `fetch_data.py`, tests, `SYSTEM_PROMPT`.

## Verification

`pytest -q`, then a Streamlit `AppTest` smoke run (default load, each disease, county pick, AI button with no LLM configured). Map click in a real browser cannot be run by AppTest and is checked manually by the user.
