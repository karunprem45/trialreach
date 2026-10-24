# Implementation Plan: Story Page

## Tasks

- [x] 1. Theme: update `.streamlit/config.toml` (colors, Google Fonts)
  - _Requirements: 4.1, 4.2_
- [x] 2. `ui.py`: pretty, plain, cached data, disease picker, CSS, cards, footer
  - _Requirements: 3.1 to 3.3, 4.x, 6.x, 7.1_
- [x] 3. `app.py`: page config (no emoji), CSS, brand header, `st.navigation`, footer
  - _Requirements: 1.1, 1.3, 7.1_
- [x] 4. Move the Map / County brief / AI outreach tabs to `page_explore.py`; plain words, no emoji
  - _Requirements: 1.1, 3.1, 3.3_
- [x] 5. Move Site Scout to `page_scout.py`
  - _Requirements: 1.1, 7.4_
- [x] 6. `page_story.py`
  - [x] 6.1 Sections 01 and 02 (map, bar chart)
  - [x] 6.2 Sections 03 and 04 (top towns, simulation)
  - [x] 6.3 Section 05 (page links), edge cases, sources caption
  - _Requirements: 2.1 to 2.6, 5.x, 7.2_
- [x] 7. Verify
  - [x] 7.1 `pytest -q`
  - [x] 7.2 AppTest smoke check of all 3 pages (not committed)
- [x] 8. Git: branch `feature/story-page`, author Dheepak, commit, push, PR, merge
