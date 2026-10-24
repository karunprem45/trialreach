# Implementation Plan: TrialReach

## Overview

Python 3.14 in `.venv/`. Flat structure: `fetch_data.py`, `deserts.py`, `llm.py`, `app.py`, `tests/`. Build in order: dependencies, data download, scoring, LLM, UI, tests, hooks, README, final check. Never open files in `data/`; use the schemas in `docs/03-data-sources.md`. Never run `streamlit run`, `git commit` or `git push`.

## Tasks

- [x] 1. Create requirements.txt
  - [x] 1.1 Write `requirements.txt` with requests, truststore, pandas, numpy, streamlit, plotly, pytest, hypothesis
    - Pin exact versions installed in `.venv/`
    - Add no LLM SDK yet; add only the one actually used when `llm.py` is finished (task 4)
    - _Requirements: 6.11_

- [x] 2. Build fetch_data.py and download the data
  - [x] 2.1 Write the helpers in `fetch_data.py`
    - Call `truststore.inject_into_ssl()` in `try/except ImportError` before any request
    - `get(url, params)`: 60 s timeout, 3 retries, raise after the last failure
    - `arcgis_pages(url, params)`: page with `resultOffset` and `resultRecordCount=1000` until fewer than 1000 rows and no `exceededTransferLimit`
    - _Requirements: 1.2, 1.3, 1.14_
  - [x] 2.2 Write `fetch_trials`, the dataset downloads and `main()`
    - Trials: `query.locn=Massachusetts`, `filter.overallStatus=RECRUITING`, `pageSize=1000`, the 9 disease search terms, requested fields, follow `nextPageToken`; keep only MA locations with a geoPoint; save slim records keyed by measure id
    - Towns: save `towns.geojson` and `towns.json` with `INTPTLAT20` and `INTPTLON20` cast to float
    - CDC PLACES: MA, crude prevalence, 9 measure ids
    - Hospitals: lat/lon from geometry y/x, null beds stored as 0
    - EJ: only `EJ='Yes'` block groups
    - Write `fetched_at.txt`; on a failed dataset print its name and exit with status 1
    - _Requirements: 1.1, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 1.12, 1.13_
  - [x] 2.3 Run `.venv/bin/python fetch_data.py` once and report counts
    - Report the number of towns, CDC rows, hospitals, EJ rows and trials per disease (use a short script that prints `len()` only; do not print or open the data files)
    - Expected: 351 towns, 126 CDC rows, 103 hospitals, 9 trial keys
    - _Requirements: 1.1, 1.12_

- [x] 3. Build deserts.py
  - [x] 3.1 Implement `load_all()` and `miles()`
    - `load_all()` reads only Saved_Data and returns towns, shapes, places, trials, hospitals, ej (joined to towns by upper-cased MUNICIPALITY, with county column), fetched_at
    - `miles()`: haversine, Earth radius 3958.8, scalars or numpy arrays
    - Define `REACH_MILES = 25` and `CONDITIONS` for the 9 diseases
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 3.2 Implement `trial_sites()` and `town_access()`
    - `trial_sites`: one row per trial and MA site, county of the nearest town center
    - `town_access`: add `nearest_miles` and `trials_in_reach` (distinct NCT ids within 25 miles) using numpy broadcasting, no pair loops
    - With no sites, keep values finite (large fallback for miles, 0 trials)
    - _Requirements: 2.4, 3.1, 3.2, 3.3_
  - [x] 3.3 Implement `desert_score()` and `county_scores()`
    - `desert_score(affected, trials_in_reach)` returns `(people_per_trial, score)`; score = round(100 × ppt ÷ max ppt); guard division by zero
    - `county_scores(d, mid)` returns `(county_df, towns_with_access, sites)`: 14 rows, worst first, population-weighted means by POP2020, prevalence, CDC low/high, trials in county, People_Per_Trial
    - All 9 diseases in under 2 seconds
    - _Requirements: 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10_
  - [x] 3.4 Implement `candidate_hospitals()`, `ej_summary()` and `outreach_brief()`
    - Hospitals: "Acute Hospital" only, `beds` = ICU + MED_SURG + PEDIATRIC, `nearest_trial_miles`, sorted by beds descending
    - EJ: total EJ residents plus per-town table (EJ population, neighborhoods, population-weighted limited-English %)
    - Brief: non-empty markdown from disease, county row, state prevalence, hospitals and EJ data; say "talk to your doctor or the study team", never that a person qualifies
    - _Requirements: 5.4, 5.6, 5.8, 7.2_

- [x] 4. Build llm.py
  - [x] 4.1 Implement `generate(prompt, system="") -> str | None`
    - `LLM_PROVIDER=bedrock`: Bedrock Converse API with model `LLM_MODEL`
    - `LLM_PROVIDER=anthropic`: Anthropic API with `ANTHROPIC_API_KEY` and model `LLM_MODEL`
    - Unset or other provider, any exception, or a call over 20 seconds: return `None`, never raise
    - Read credentials only from environment variables; import the SDK inside the provider branch
    - Add only the SDK in use to `requirements.txt`
    - _Requirements: 6.5, 6.6, 6.7, 6.10, 6.11, 8.3_

- [x] 5. Build app.py
  - [x] 5.1 Page setup, data loading, sidebar, header and metrics
    - `st.set_page_config` with title "TrialReach", icon "🌵", wide layout
    - Cache `load_all` and `county_scores`; if a Saved_Data file is missing show a message to run `fetch_data.py` and `st.stop()`
    - Sidebar: disease selectbox (9), "Color the map by" radio, "Show trial sites" (on), "Show acute hospitals" (off), one-sentence score explanation
    - Subtitle and four metrics (trial count, Suffolk share, worst county with People_Per_Trial, gap vs Boston with Suffolk number as small text)
    - Title Case for UPPERCASE place names
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.12, 4.13, 8.1, 8.2, 8.4_
  - [x] 5.2 Map and ranking table
    - `go.Choroplethmap` on `towns.geojson`, `featureidkey="properties.TOWN20"`, "Reds", white 0.3 px borders
    - Score mode: county score 0–100; miles mode: `nearest_miles` with max at the 98th percentile
    - Blue `go.Scattermap` trial dots (deduplicated by facility, lat, lon); green hospital dots
    - `map_style="carto-positron"`, center (42.15, -71.75), zoom 6.9, height 560, scroll zoom off
    - Ranking table of 14 counties with Desert Score progress bar 0–100
    - _Requirements: 4.5, 4.6, 4.7, 4.8, 4.9, 4.10, 4.11_
  - [x] 5.3 County deep dive
    - "Look closer at a county" selectbox defaulting to the worst county
    - Rule_Brief and CDC 95% range caption
    - 8 nearest recruiting trials from the county's population-weighted center, with an "Open" link to `https://clinicaltrials.gov/study/{nct}`
    - Candidate hospitals table and top 10 EJ towns under "Where outreach has to try harder"
    - `st.info` with a friendly message for empty hospitals, trials or EJ towns
    - _Requirements: 5.1, 5.2, 5.3, 5.5, 5.7, 5.9_
  - [x] 5.4 AI brief with fallback
    - Language selectbox (English, Spanish, Portuguese, Haitian Creole, Chinese) and "Write recruitment brief" button
    - Prompt contains only the allowed facts; system prompt carries the safety rules
    - Show Resident_Flyer (≤120 words, grade 6) and Hospital_Note (3 short English lines) when text returns
    - On `None`, show the Rule_Brief and the caption "AI brief unavailable — showing the standard recommendation."
    - Cache in `st.session_state` by (county, disease, language)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.8, 6.9, 8.3_
  - [x] 5.5 Footer
    - Footer text "TrialReach scores places, never people. Not medical advice. Distances are straight-line from town centers. Licensed beds are not live occupancy."
    - Links to ClinicalTrials.gov (U.S. NLM), CDC PLACES 2023 county crude prevalence and MassGIS (Census 2020 towns, hospitals, EJ 2020 block groups)
    - Plain, simple language on screen
    - _Requirements: 7.1, 7.3, 7.4, 7.5_

- [x] 6. Write the tests
  - [x] 6.1 Write `tests/test_deserts.py` (U1–U7)
    - U1 `miles(42.36, -71.06, 42.10, -72.59)` between 75 and 85
    - U2 `county_scores` returns 14 counties for each of the 9 diseases
    - U3 every score 0–100 and max equals 100
    - U4 no missing prevalence and every town has `nearest_miles`
    - U5 `candidate_hospitals`, `ej_summary`, `outreach_brief` run for every disease and county; brief non-empty
    - U6 Hampden diabetes People_Per_Trial more than 10× Suffolk
    - U7 `generate()` returns `None` with no LLM environment variables
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8_
  - [x] 6.2 Write property test for score range (`tests/test_properties.py`)
    - **Property 1: Scores are in range and the worst county scores 100**
    - Tag: `# Feature: trialreach, Property 1: ...`; `@settings(max_examples=100)`
    - **Validates: Requirements 3.7, 3.10, 9.9**
  - [x] 6.3 Write property test for more trials
    - **Property 2: More trials never raise People_Per_Trial**
    - **Validates: Requirements 3.6, 9.10**
  - [x] 6.4 Write property test for more affected people
    - **Property 3: More affected people never lower People_Per_Trial**
    - **Validates: Requirements 3.6, 9.11**
  - [x] 6.5 Write property test for distance
    - **Property 4: Distance is symmetric and zero to itself**
    - **Validates: Requirements 2.3, 9.12**
  - [x] 6.6 Write property test for trial JSON round trip
    - **Property 5: Trial record JSON round trip**
    - **Validates: Requirements 1.7, 9.13**

- [x] 7. Create the two agent hooks in `.kiro/hooks/`
  - [x] 7.1 H1 Tests on save
    - Trigger: file saved for `deserts.py`, `llm.py`, `tests/**/*.py`
    - Wording from `docs/09-kiro-playbook.md` section 3: run `python -m pytest -q` in `.venv`; one line if all pass; on failure show only failing test names and the assertion line; do not edit files
    - _Requirements: 9.1_
  - [x] 7.2 H2 Pre-commit check
    - Manual trigger; wording from `docs/09-kiro-playbook.md` section 3 (git user.name, no keys in tracked files, `.kiro/` not ignored, requirements.txt complete, pytest passes; 5-line checklist, no edits)
    - _Requirements: 6.10, 9.1_

- [x] 8. Write README.md
  - [x] 8.1 Write `README.md`
    - Sections: problem, finding, score formula, features, data links, setup, run (`streamlit run app.py`, for the user to run), tests, limits
    - Include the places-not-people and not-medical-advice statements and the three data sources
    - _Requirements: 7.1, 7.2, 7.4, 8.1_

- [x] 9. Final checkpoint - Run `.venv/bin/python -m pytest -q`
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- No tasks are optional; all tests are required.
- Each task references specific requirements for traceability.
- Tasks 2.3 and 9 run commands; do not run `streamlit run`, `git commit` or `git push`.
- Property tests validate the universal properties P1–P5 from the design; unit tests U1–U7 cover examples and edge cases.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "4.1"] },
    { "id": 2, "tasks": ["2.2"] },
    { "id": 3, "tasks": ["2.3"] },
    { "id": 4, "tasks": ["3.1"] },
    { "id": 5, "tasks": ["3.2"] },
    { "id": 6, "tasks": ["3.3"] },
    { "id": 7, "tasks": ["3.4"] },
    { "id": 8, "tasks": ["5.1", "6.1", "6.2", "7.1", "7.2"] },
    { "id": 9, "tasks": ["5.2", "6.3"] },
    { "id": 10, "tasks": ["5.3", "6.4"] },
    { "id": 11, "tasks": ["5.4", "6.5"] },
    { "id": 12, "tasks": ["5.5", "6.6"] },
    { "id": 13, "tasks": ["8.1"] }
  ]
}
```
