# Implementation Plan: UI Polish

## Tasks

- [x] 1. Add `.streamlit/config.toml` with the theme
  - _Requirements: 4.1_
- [x] 2. Hero in `app.py`
  - [x] 2.1 Remove the sidebar; move the disease selector to the main page
  - [x] 2.2 Add `story_line`, the 4 stat cards with help tooltips and the data caption
  - _Requirements: 1.1 to 1.4, 6.1_
- [x] 3. Tabs and map
  - [x] 3.1 Create the three tabs; Map tab = controls, map, ranking
  - [x] 3.2 OrRd colorscale, colorbar title, legend, county outline
  - [x] 3.3 Map click selects the county; picker selectbox stays as fallback
  - _Requirements: 2.1, 2.2, 3.1 to 3.3, 4.2, 4.3_
- [x] 4. County brief tab (recommendation, trials, hospitals, EJ) with empty states
  - _Requirements: 2.3, 5.2_
- [x] 5. AI outreach tab: spinner, bordered flyer, download button, hospital note, fallback
  - _Requirements: 2.4, 5.1, 5.3, 7.2, 7.3_
- [x] 6. Small-screen CSS; keep footer safety text
  - _Requirements: 6.2, 6.3, 7.1_
- [x] 7. Verify
  - [x] 7.1 `pytest -q`
  - [x] 7.2 AppTest smoke check (not committed)
- [ ] 8. Git: branch `feature/ui-polish`, author Dheepak, commit, push, PR, merge
