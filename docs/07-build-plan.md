# 07 · Build Plan with Kiro (sessions, prompts, credit budget)

Budget: 2,000 Kiro credits (one account). Target spend: **≤ 300**, keep the rest as safety margin.

## Credit-saving rules (follow every session)
1. **One feature = one new chat session** (+ button in chat). Long chats re-send history every turn = more credits.
2. **Reference docs with `#`** (e.g. `#docs/03-data-sources.md`) instead of pasting text. Attach only the doc the step needs.
3. **Pick the model per task** (model menu next to "Auto"):
   | Task type | Model | Why |
   |---|---|---|
   | Spec generation + core code (S1, S2, S5, S6) | Claude Sonnet 5.5 (1.3×) | accurate first time = fewer retries |
   | Small fixes, hooks, README, docs (S3, S4, S7) | Claude Haiku 5.5 (0.06×) | ~20× cheaper |
   | Avoid unless stuck | Opus (2×) | expensive |
4. **Run commands yourself** in the terminal (`python fetch_data.py`, `pytest`, `streamlit run app.py`). Don't ask Kiro to run long commands.
5. **Never let Kiro read `data/`.** Steering already says so. If it tries, click Deny.
6. **Paste only the error's last ~15 lines** when asking for a fix, not the whole terminal.
7. **Review the spec before running tasks.** Fixing a wrong requirement costs 1 message; fixing wrong code costs many.
8. Check credits after each session (status bar). Write the number in the log at the bottom.

## Who does what (run `bash scripts/as-<name>.sh` before each session; full rules in docs/09 §5)
| Session | Owner |
|---|---|
| S1 data, S2 scoring, S6 AI brief | Karuniya |
| S3 hook, S4 property tests, S5 app UI, S7 README/KIRO.md | Dheepak |

## Sessions
Each session: **Spec mode** → paste prompt → review requirements/design/tasks → run tasks → you run the check → commit + push.

### S1 · Data download (Spec: Sonnet for the spec, Auto for tasks; uses Fetch MCP)
```
First use the fetch MCP to get a 2-record sample from ClinicalTrials.gov (pageSize=2) and CDC PLACES ($limit=2) to confirm field names. Then create a spec for fetch_data.py exactly as described in #docs/03-data-sources.md and #docs/02-architecture.md (section 1).
Keep it one file, simple functions, retries, paging, slimming the trials. Do not read data/.
```
Check: `python fetch_data.py` prints counts ≈ 351 / 351 / 126 / trials per disease / 103 / 2604. Commit `S1 fetch data` (include data/).

### S2 · Scoring (Spec, Sonnet)
```
Create a spec for deserts.py and tests/test_deserts.py following #docs/02-architecture.md (sections 2–3)
and unit tests U1–U6 in #docs/06-test-plan.md. Put the score formula in a small pure helper so it can be
property-tested later. Do not read data/; use the schemas in #docs/03-data-sources.md.
```
Check: `python -m pytest -q` passes; Hampden diabetes ≈ 18,000 vs Suffolk ≈ 860. Commit `S2 scoring`.

### S3 · Agent hooks + MCP config (Haiku)
Create hooks H1 and H2 exactly as in docs/09 §3. (MCP was already set up and committed by Karuniya in S1.)
Check: save deserts.py → tests run; click H2 → 5-line checklist. Commit `S3 hooks` (the .kiro/hooks files).

### S4 · Property tests (quick-spec skill, Haiku)
```
Add tests/test_properties.py with Hypothesis properties P1–P4 from #docs/06-test-plan.md, using the pure
score helper in deserts.py. Add hypothesis to requirements.txt.
```
Check: pytest passes. Note in KIRO.md whether Hypothesis found anything. Commit `S4 property tests`.

### S5 · App UI (Spec, Sonnet)
```
Create a spec for app.py following #docs/04-ui-spec.md, using only functions from deserts.py.
Skip the AI brief controls for now (separate spec). Add streamlit and plotly to requirements.txt.
```
Check: `streamlit run app.py` → demo checks 1–3 in docs/06. Commit `S5 app`.

### S6 · AI brief (Spec, Sonnet)
First get the provider + key from organizers. Then:
```
Create a spec for llm.py and the AI recruitment brief in app.py following #docs/05-ai-brief.md
(not the stretch agent). Must fall back safely with no key. Add unit test U7 from #docs/06-test-plan.md.
```
Set keys in the terminal only (e.g. `export LLM_PROVIDER=...`). Never commit keys.
Check: Hampden + Spanish brief works; with keys unset, the fallback shows. Commit `S6 AI brief`.

### S7 · README + Kiro write-up (Vibe, Haiku)
```
Write README.md (problem, key finding, score formula, features, data sources with links, setup and run
steps, tests, limits) using #docs/01-PRD.md and #docs/02-architecture.md. Then create KIRO.md from the
template in #docs/08-submission.md, filling in the facts from this repo's .kiro folder.
```
Then edit KIRO.md yourselves with real experiences. Commit `S7 docs`.

### S8 · Optional stretch: Site Scout agent (Sonnet), only if S1–S7 are done before ~5 PM
```
Create a spec for the optional "Site Scout" agent in #docs/05-ai-brief.md (stretch section).
```

## Credit log
| Session | Model | Credits before | after | used |
|---|---|---|---|---|
| Steering | Auto | | | 0.83 |
| S1 | | | | |
| S2 | | | | |
| S3 | | | | |
| S4 | | | | |
| S5 | | | | |
| S6 | | | | |
| S7 | | | | |
