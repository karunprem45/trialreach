# 02 · Architecture & Design

## 1. Data flow
```
fetch_data.py ──► data/*.json ──► deserts.py (pure functions) ──► app.py (Streamlit UI)
                                         └──► llm.py (optional AI brief, with fallback)
```
Run `fetch_data.py` once. The app only reads `data/`.

## 2. Module: deserts.py (no Streamlit imports)
| Function | Input | Output |
|---|---|---|
| `load_all()` | – | dict: `towns` (DataFrame: town, county, pop, lat, lon), `shapes` (GeoJSON), `places` (DataFrame), `trials` (dict measure→list), `hospitals` (DataFrame), `ej` (DataFrame with `county` added by joining MUNICIPALITY.upper() to town), `fetched_at` (str) |
| `miles(lat1, lon1, lat2, lon2)` | floats or numpy arrays (broadcasts) | haversine miles, Earth radius 3958.8 |
| `trial_sites(d, mid)` | data, measure id | DataFrame, one row per (trial, MA site): nct, title, phase, facility, city, lat, lon, county. County = county of the **nearest town center**. |
| `town_access(d, sites)` | data, sites | towns + `nearest_miles` (min distance to any site) + `trials_in_reach` (count of **distinct** NCT ids with a site ≤ 25 mi) |
| `county_scores(d, mid)` | data, measure id | (county DataFrame, towns, sites); see §3 |
| `candidate_hospitals(d, county, sites)` | | acute hospitals in county (`FACILITY_TYPE == "Acute Hospital"`), `beds = ICU+MED_SURG+PEDIATRIC`, `nearest_trial_miles`, sorted by beds desc |
| `ej_summary(d, county)` | | (total EJ residents int, DataFrame by town: ej_pop, neighborhoods, limited_english_pct = population-weighted mean of LIMENGHHPCT) |
| `outreach_brief(condition, row, state_prev, hospitals, ej_pop, ej_towns)` | | markdown string, rule-based recommendation (also the AI fallback) |

Constants: `REACH_MILES = 25`; `CONDITIONS = {measure_id: label}` for the 9 diseases in docs/03.

## 3. Research Desert Score (per county, per disease)
```
pop                = sum of town POP2020 in county
avg_miles          = population-weighted mean of town nearest_miles
trials_in_reach    = population-weighted mean of town trials_in_reach
trials_in_county   = distinct NCT ids with a site in the county
prevalence         = CDC PLACES data_value (%)
affected           = prevalence / 100 × CDC totalpopulation
people_per_trial   = affected / (trials_in_reach + 1)          # +1 keeps zero-trial counties finite
score              = round(100 × people_per_trial / max(people_per_trial))   # worst county = 100
```
Sort worst first. Also keep CDC `low_confidence_limit` / `high_confidence_limit` as prev_low / prev_high.

**Why this formula (put in write-up):** a distance-only score made Hampden look fine (one site 6 miles
away) even though only 2 trials serve ~56,000 people. "People per nearby trial" captures both distance
and choice, and is easy to explain.

## 4. Module: llm.py
One function: `generate(prompt: str) -> str | None`.
- Provider and model come from environment variables (see docs/05). No keys in code.
- Any error, timeout (20 s) or missing key → return `None`. Caller then uses `outreach_brief()`.

## 5. Module: app.py
UI only; layout in docs/04-ui-spec.md. Wrap `load_all` and `county_scores` in `st.cache_data`.

## 6. Non-functional
- Offline: app works from `data/` (~1.5 MB total).
- Performance: all 9 diseases × 14 counties compute in < 2 s (numpy broadcasting, no Python loops over distance pairs).
- Privacy: only public, place-level data.
