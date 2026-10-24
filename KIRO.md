# How we used Kiro

TrialReach (Hackachusetts 2026, Healthcare & Biotech, challenge H5) finds the research deserts of Massachusetts: counties where many adults have a disease but few recruiting clinical trials are nearby. Live app: https://trialreach.streamlit.app

## Tools
Kiro IDE only: Spec mode, Default (Vibe) mode, steering, agent hooks, MCP, a slash command and the built-in web fetch. We did not use Kiro powers.

We drafted the planning docs (`docs/01` to `docs/09`) with an AI assistant first. Kiro then wrote all the application code from those docs.

## Steering
Three short files in `.kiro/steering/`: `product.md`, `tech.md`, `structure.md`. Together they are under 400 words, on purpose, because steering is sent with every request.

Rules we put in them:
- Score places, never people. Never say someone qualifies for a trial.
- Always cite sources (ClinicalTrials.gov, CDC PLACES, MassGIS).
- Never read `data/` (large JSON). Use the schemas in `docs/03-data-sources.md`.
- Do not run long-running commands. We run `streamlit run` and `fetch_data.py` ourselves.
- Company git workflow: one branch per task, PR, merge commit.

Biggest wins: "never read `data/`" kept requests small. The git workflow rule made Kiro create the branch, open the PR and merge it without being asked each time.

## Spec-driven development
There are four specs in `.kiro/specs/`, each with requirements, design and tasks:
- `trialreach`: the whole app in one run (requirements in EARS notation).
- `ui-polish`: hero sentence, tabs, map click, small-screen layout.
- `site-scout`: the what-if simulator and the Site Scout agent.
- `story-page`: the five-section Story page and multipage navigation.

`fetch_data.py` worked on the first run and every count matched `docs/03`: 351 towns, 126 CDC rows, 103 hospitals, 2,604 environmental-justice block groups and 1,621 trials across the 9 disease searches.

Specs vs. vibe: we used specs for multi-file features, which meant fewer retries and a plan we could review before any code changed. We used Default mode for small fixes: the Groq provider, answer truncation, tool field names, bar-chart labels and the dark theme.

## Agent hooks
- H1 runs `pytest` when `deserts.py`, `llm.py` or anything in `tests/` is saved. It fired automatically during several changes.
- H2 is a pre-commit checklist (author name, no keys in tracked files, `.kiro/` not ignored, requirements complete, tests pass). Kiro migrated it to the new format, and it is now the `/pre-commit-check` slash command (`.kiro/steering/pre-commit-check.md`, manual inclusion), so it costs nothing until we call it. The older hook file is still in `.kiro/hooks/`.

## MCP and web fetch
- The fetch MCP server confirmed the CDC PLACES field names from a 2-record sample (response length capped).
- ClinicalTrials.gov's `robots.txt` blocks automated API fetching. Kiro respected that and used the field names we had already verified in `docs/03`.
- Kiro also read `docs.streamlit.io` before building the multipage navigation.

## Property-based testing
Hypothesis checks six properties, and all tests pass:
1. The score is always 0 to 100, and the worst county scores 100.
2. Adding a trial never makes a county worse.
3. More patients never improve a county.
4. Distance is symmetric, and the distance from a point to itself is zero.
5. Trial JSON survives a round trip.
6. Adding a simulated site never increases any county's people per trial.

## Safety in code
Site Scout replaces any AI answer that says "qualifies" or "eligible", or that cites a number not found in its tool results, with a rule-based answer built from the tool results. Scoring is per county and per town, with no personal health data.

## Git
One branch per task. Pull requests #1 to #18 were merged with merge commits. Authorship is split between Karuniya and Dheepak with `scripts/as-karuniya.sh` and `scripts/as-dheepak.sh`, because we share one laptop.

## Credit management
Budget: 2,000 credits. The whole build used about 80.
- Sonnet 5.5 at medium effort for specs and multi-step work.
- Haiku 5.5 for docs and small edits.
- We never used Opus or GPT Sol.
- Techniques: short steering, no reading of `data/`, one task per branch, and running long commands ourselves.

## Stack and deployment
Python, pandas, numpy, Streamlit (multipage, dark theme, CSS motion), Plotly, and Groq (`openai/gpt-oss-120b`) for the optional AI brief, with an offline fallback when no key is set. It is deployed on Streamlit Community Cloud and redeploys on every merge.

## Demo video
Recorded from the live app and edited with an AI assistant, not built in Kiro. It is in `media/` and on YouTube.
