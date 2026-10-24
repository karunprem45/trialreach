# 08 · Submission Checklist, Kiro Write-up Template, Video Script

## Checklist (SundAI, before 8:00 PM — aim for 7:30)
- [ ] Team members added on SundAI (Karuniya Premnath, Dheepak Karan)
- [ ] Track: Healthcare & Biotech
- [ ] Text description (features + how it works)
- [ ] Public GitHub repo URL: https://github.com/karunprem45/trialreach
- [ ] `.kiro/` folder is in the repo root on GitHub (NOT in .gitignore)
- [ ] README has setup + run steps; `data/` committed so it runs offline
- [ ] Demo video < 3 min, public/unlisted on YouTube, link in the form, no copyrighted music
- [ ] Kiro write-up (KIRO.md, also pasted into the form if asked)
- [ ] No API keys anywhere in the repo (`git grep -i "key"` before final push)

## KIRO.md template (fill with what really happened)
```
# How we used Kiro

## Tools
Kiro IDE (chat in Spec and Vibe modes, steering, agent hooks). [Add CLI/Web if used.]

## Steering
- product.md: goal, users, safety rules (score places not people, never claim eligibility, cite sources).
- tech.md: stack + "save credits" rules (never read data/, don't run long commands, smallest change).
- structure.md: flat layout. Biggest difference: ______

## Spec-driven development
We wrote planning docs first (docs/01–07), then created one Kiro spec per feature:
fetch_data (S1), scoring (S2), app UI (S5), AI brief (S6). Each spec: requirements → design → tasks.
What it improved: ______ . Compared with vibe coding (used for small fixes): ______

## Agent hooks
On save of deserts.py or tests/ → run pytest. It caught: ______

## Property-based testing
Hypothesis properties P1–P4 (score range, more trials never worse, symmetry of distance). Found: ______

## MCP / Powers
[Only if used. Otherwise: "Not used; our data comes from public REST APIs called by our own code."]

## Credit management
Budget 2,000 credits. Used ____ . Techniques: one session per feature, #doc references instead of pasting,
Haiku for small tasks and Sonnet for specs, running commands ourselves, steering that forbids reading data/.
```

## Demo video script (≈ 2:30)
| Time | Show | Say |
|---|---|---|
| 0:00 | Title screen | "Food deserts have a name. Research deserts don't." |
| 0:10 | Metrics row | "Springfield has the highest diabetes rate in Massachusetts, but about 18,000 people share each nearby trial. In Boston it's about 860 — a 21× gap." |
| 0:35 | Map, then switch disease | "TrialReach scores every county for 9 diseases using ClinicalTrials.gov, CDC and MassGIS data." |
| 1:05 | Click Hampden | "For each research desert it shows the nearest trials, a hospital that could host a study, and where outreach needs translation." |
| 1:35 | AI brief in Spanish | "One click writes a recruitment flyer in the community's language." |
| 2:00 | Kiro: specs, hooks, steering | "We built it in Kiro with spec-driven development, steering rules and a test hook." |
| 2:20 | Footer | "TrialReach scores places, never people. It tells researchers where the next trial should go." |
