# 09 · Kiro Playbook: features, model routing, team rules

The rules require "next-level" use of Kiro. This is where each feature is used, so KIRO.md can describe it.

## 1. Feature map
| Kiro feature | Where we use it | Session |
|---|---|---|
| **Steering** (`.kiro/steering/`) | product.md, tech.md, structure.md: always loaded. Kept under 300 words total because steering is sent with every request. | done |
| **Specs** (`.kiro/specs/`) | One spec per feature: requirements → design → tasks | S1, S2, S5, S6 |
| **Agent hooks** (`.kiro/hooks/`) | H1 run tests on save, H2 manual pre-commit check | S3 |
| **Skills** (Global: quick-spec, bug-fix, architecture-selection) | `quick-spec` for the small property-test feature (S4); `bug-fix` whenever a test or the app errors | S4, any fix |
| **MCP** (`.kiro/settings/mcp.json`) | Fetch MCP so Kiro can look at a tiny live API sample before writing fetch_data.py | S1 |
| **Property-based testing** | Hypothesis properties P1–P4 (docs/06) | S4 |
| **Vibe mode** | Small fixes and docs only | S7, fixes |
| **Powers** | Optional. Only list in KIRO.md if actually used. | – |

## 2. Model routing (cost per request multiplier, from the Kiro model menu)
| Model | Cost | Use it for |
|---|---|---|
| Claude Haiku 5.5 | **0.06×** | Hooks, README, KIRO.md, small edits, explaining an error, renaming, formatting |
| GPT 5.6 Luna | 0.6× | Backup cheap model if Haiku struggles on a small task |
| Auto | 1× | Running spec **tasks** (writing the code) |
| Claude Sonnet 5.5 | 1.3× | Writing the **spec** itself (requirements + design + tasks) for S1, S2, S5, S6 |
| Claude Opus 5.5 | 2× | Only if Sonnet fails the same task twice |
| GPT 5.6 Terra / Kimi K3 / GPT 5.6 Sol | 2.2× / 2.4× / 4.4× | Do not use |

Rule of thumb: **plan with Sonnet, build with Auto, polish with Haiku.**
Switch the model in the chat box dropdown before sending each message.

## 3. Hooks
Create in the Agent Hooks panel → **Create New Hook**. Pick the trigger and paste the instruction.

**H1 · Tests on save** · trigger: *File saved*, pattern `deserts.py`, `llm.py`, `tests/**/*.py`
> Run `python -m pytest -q` in the project's .venv. If all pass, reply with one line. If something fails, show only the failing test names and the assertion line. Do not edit any files.

If the hook editor offers a plain **run command** action, use that instead (no AI credits).
Otherwise set the hook's model to **Haiku** so each save costs ~0.06×.

**H2 · Pre-commit check** · trigger: *Manual* (click it before each push)
> Check, without editing files: (1) `git config user.name` and show it, (2) no API keys or tokens in tracked files, (3) `.kiro/` is not in .gitignore, (4) requirements.txt lists every imported third-party package, (5) `python -m pytest -q` passes. Reply with a 5-line checklist.

## 4. MCP: Fetch server (one-time setup, ~2 min)
1. Terminal (venv active): `pip install uv`, which gives you `uvx`.
2. Kiro panel → **MCP SERVERS** → open the config (or create `.kiro/settings/mcp.json`) with:
```json
{
  "mcpServers": {
    "fetch": {
      "command": "/Users/karuniyapremnath/claude_project/trailreach/trialreach/.venv/bin/uvx",
      "args": ["mcp-server-fetch"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```
3. The MCP panel should show **fetch** with a green dot.
4. Use in S1 only, with **tiny samples** (credits!): ask Kiro to fetch ClinicalTrials.gov with `pageSize=2`
   and CDC with `$limit=2` to confirm field names, then write fetch_data.py.
   For the write-up: "MCP let Kiro check real API responses instead of guessing field names."

## 5. Team rules: one laptop, two contributors
GitHub credits each commit by its **author email**, not by who pushed. So one laptop works.

| Person | GitHub | Commit email |
|---|---|---|
| Karuniya Premnath | karunprem45 | 135019427+karunprem45@users.noreply.github.com |
| Dheepak | dheepakkaran | 67942227+dheepakkaran@users.noreply.github.com |

**Before every session, the person at the keyboard runs their script:**
```bash
bash scripts/as-karuniya.sh
bash scripts/as-dheepak.sh
```
(run only the one for the person at the keyboard). Each prints who is now set. Then commit in Source Control as normal.
Pushing always uses the laptop's GitHub login; that's fine, authorship stays correct.

**Split (about half each):**
| Commit | Owner |
|---|---|
| setup, steering, docs | Karuniya |
| S1 fetch data | Karuniya |
| S2 scoring | Karuniya |
| MCP config (before S1, committed with S1) | Karuniya |
| S3 hooks | Dheepak |
| S4 property tests | Dheepak |
| S5 app UI | Dheepak |
| S6 AI brief | Karuniya |
| S7 README + KIRO.md | Dheepak |
| final fixes | whoever does them |

**Work done together:** add a blank line and then a trailer at the end of the commit message:
```
Co-authored-by: Dheepak <67942227+dheepakkaran@users.noreply.github.com>
```
(or Karuniya's line if Dheepak is the author).

**Kiro must never commit or push.** Only the two of you commit, so every commit carries a real author.

**Check:** GitHub → repo → Insights → Contributors shows exactly two people.

## 6. Credit budget per session (estimate)
| Session | Model plan | Est. credits |
|---|---|---|
| S1 data + MCP sample | Sonnet spec, Auto tasks | 15–30 |
| S2 scoring + tests | Sonnet spec, Auto tasks | 20–40 |
| S3 hooks | Haiku | 1–3 |
| S4 property tests | Haiku/quick-spec | 2–5 |
| S5 app UI | Sonnet spec, Auto tasks | 30–60 |
| S6 AI brief | Sonnet spec, Auto tasks | 15–30 |
| S7 docs | Haiku | 1–3 |
| Fixes buffer | mixed | 50 |
| **Total** | | **≈ 135–220 of 2,000** |
