# 06 · Test Plan (tests/)

Run: `python -m pytest -q`. Tests read the saved `data/`, no network.

## Unit tests (tests/test_deserts.py)
| ID | Test | Expected |
|---|---|---|
| U1 | `miles(42.36, -71.06, 42.10, -72.59)` (Boston→Springfield) | 75–85 |
| U2 | For each of the 9 diseases: `county_scores` returns 14 counties | len == 14 |
| U3 | Scores in range, worst = 100 | 0 ≤ score ≤ 100, max == 100 |
| U4 | No missing prevalence; every town has nearest_miles | no NaN |
| U5 | For every disease × county: candidate_hospitals, ej_summary, outreach_brief run without error | non-empty brief |
| U6 | Headline fact | Hampden diabetes people_per_trial > 10 × Suffolk |
| U7 | llm.generate with no env vars | returns None (no exception) |

## Property-based tests (tests/test_properties.py, Hypothesis)
Build small synthetic inputs (random prevalence 1–40 %, populations 1k–1M, trial counts 0–200) and call
the score math directly (factor the formula into a small pure helper, e.g. `desert_score(affected, trials_in_reach)` → scores).
| ID | Property |
|---|---|
| P1 | Every score is between 0 and 100 and the maximum is exactly 100 |
| P2 | Adding trials to one county never increases that county's people_per_trial |
| P3 | Increasing affected people in one county never decreases its people_per_trial |
| P4 | `miles(a, b) == miles(b, a)` and `miles(a, a) == 0` (symmetry, identity) |

## Agent hook (Kiro)
"When `deserts.py` or anything in `tests/` is saved → run `python -m pytest -q` and report failures."

## Manual demo checks
1. Diabetes: Hampden is #1, gap ≈ 20×. 2. Miles mode: Berkshire/Cape darker than Boston.
3. Every disease loads without error. 4. AI brief in Spanish for Hampden; fallback with no key.
