# 01 · Product Requirements (PRD) — TrialReach

**Owner:** Karuniya Premnath, Dheepak Karan · **Event:** Hackachusetts 2026 · **Track:** Healthcare & Biotech (H5)

## 1. Problem
Massachusetts has 3,000+ recruiting clinical trials, but they cluster in Boston. Counties with the
highest disease rates often have very few trials within reach.
Example (diabetes, verified with live data on 2026-10-24):

| County | Adults with diabetes | People with diabetes per recruiting trial within 25 mi |
|---|---|---|
| Hampden (Springfield) | 12.1% (highest in MA) | ≈ 18,000 |
| Suffolk (Boston) | 9.3% | ≈ 860 |

79% of recruiting diabetes trials in MA have a Boston site. This is a **research desert**.

## 2. Goal
Give research offices, trial sponsors and health officials a map that shows **where to open the next
study site and which communities to reach**, for 9 diseases.

## 3. Users
| User | Need |
|---|---|
| Hospital research office | "Should our hospital host trials for disease X?" |
| Trial sponsor (drug company) | "Where should our next site go so we reach under-served patients?" |
| State health official | "Which communities are left out of research?" |

## 4. Requirements (EARS style)
**R1 Data.** The system shall download all datasets once and save them in `data/` so the app works offline.
**R2 Diseases.** The system shall support: diabetes, obesity, depression, high blood pressure, coronary heart disease, COPD, asthma, stroke, cancer.
**R3 Score.** For each county and disease, the system shall compute the Research Desert Score defined in docs/02-architecture.md.
**R4 Map.** When the user picks a disease, the system shall color a Massachusetts town map by the county score (or by miles to the nearest trial, user toggle) and show trial sites as dots.
**R5 Ranking.** The system shall list all 14 counties worst-first with score, people per nearby trial, prevalence, trials within 25 miles, and average miles.
**R6 Headline.** The system shall show 4 metrics: trials in MA, % with a Boston (Suffolk) site, worst county, gap vs Boston.
**R7 County detail.** When the user selects a county, the system shall show: a plain-language recommendation, the 8 nearest recruiting trials with links to clinicaltrials.gov, acute hospitals in the county (largest first), and environmental-justice towns with limited-English %.
**R8 AI brief.** When the user clicks "Write recruitment brief" and picks a language, the system shall generate a short resident flyer + a 3-line note for the hospital. If no LLM key is set or the call fails, the system shall show the rule-based recommendation instead and never crash.
**R9 Safety.** The system shall never state that a person qualifies, shall say it is not medical advice, and shall cite data sources in the footer.
**R10 Tests.** The system shall have unit tests and property-based tests that pass with `python -m pytest`.

## 5. Out of scope
Patient accounts, personal health data, eligibility decisions, drive-time routing, non-MA states.

## 6. Success criteria (demo)
- App opens in < 5 s from saved data, no internet needed except map tiles.
- Diabetes view shows Hampden as the worst county and a ≈ 20× gap vs Boston.
- AI brief works in Spanish for Hampden; fallback works with no key.
