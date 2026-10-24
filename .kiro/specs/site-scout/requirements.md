# Requirements: Site Scout

## Introduction

Two additions to TrialReach. Part A is a what-if simulator: add one hypothetical trial site and see how
county scores change. Part B is the Site Scout agent: a short tool-calling loop that recommends where to
open the next study site. Both score places, never people.

## Requirements

### Requirement 1: What-if simulator (Part A)

**User Story:** As a hospital research office, I want to see what happens if a hospital opens a study,
so that I can judge whether the site would close a research gap.

#### Acceptance Criteria

1. `deserts.simulate_new_site(d, mid, lat, lon, label)` SHALL add one hypothetical trial site and return
   `(before_county_df, after_county_df)`.
2. Both tables SHALL use the standard score formula, with the after score scaled by the ORIGINAL (before)
   maximum people-per-trial, so before and after are comparable.
3. Adding a site SHALL NEVER increase any county's `people_per_trial` or `score`.
4. Both tables SHALL include a `rank` column (1 = worst) and a `newly_reached` column (residents with no
   trial within 25 miles before and one within 25 miles after; 0 in the before table).
5. The County brief tab SHALL let the user pick a candidate hospital and press
   "Simulate a new trial site here".
6. The result SHALL show the score before and after, the rank change, and the residents newly within 25 miles.

### Requirement 2: Site Scout tools and agent loop (Part B)

**User Story:** As a state health official, I want to ask "where should my next trial site go?", so that I
get a recommendation backed by the app's own numbers.

#### Acceptance Criteria

1. `llm.chat_with_tools(messages, tools)` SHALL call the groq provider with the OpenAI-compatible `tools`
   parameter and `reasoning_effort` low, and return the raw assistant message dict, or `None` on a missing
   key or any error.
2. `scout.py` SHALL expose four tools: `rank_counties(disease)`, `county_details(county, disease)`,
   `simulate_new_site(county, hospital, disease)` and `write_outreach_flyer(county, disease, language)`.
3. Every tool result SHALL be JSON-serializable.
4. The agent loop SHALL run at most 6 tool calls and return a list of steps (tool name, args, short result)
   plus a final answer.
5. The final answer SHALL cite numbers from tool results only and SHALL NEVER say a person qualifies for a trial.

### Requirement 3: Offline fallback

**User Story:** As a demo presenter, I want the agent to work with no key or network, so that the demo never fails.

#### Acceptance Criteria

1. IF no key is set or the LLM errors, THEN the agent SHALL run the same tools in a fixed order
   (worst county, details, simulate top hospital, flyer) and label the run "offline mode".
2. The fallback SHALL pick the county ranked worst by `rank_counties`.

### Requirement 4: Site Scout tab

**User Story:** As a user, I want to type or click a question and watch the agent work, so that I trust the answer.

#### Acceptance Criteria

1. The app SHALL have a "Site Scout" tab with a text input and 3 example question buttons.
2. The tab SHALL show each tool step live in `st.status`, then a final recommendation card.
3. The tab SHALL use no emojis and SHALL cite ClinicalTrials.gov, CDC PLACES and MassGIS.
