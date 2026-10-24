# 05 · AI Recruitment Brief (llm.py + app.py)

## Feature
In the county deep dive: a selectbox **Language** (English, Spanish, Portuguese, Haitian Creole, Chinese)
and a button **Write recruitment brief**. Output:
1. **Resident flyer** (≤ 120 words, in the chosen language, reading level ~grade 6)
2. **Note for the hospital research office** (3 short lines, English)

## Inputs sent to the model (facts only, no personal data)
county, disease, prevalence %, state average %, people per nearby trial, trials within 25 mi, top candidate
hospital + town, the 3 nearest trial titles with NCT ids, the EJ town with the highest limited-English %.

## Prompt rules (must be in the system prompt)
- Use only the facts given. Do not invent numbers, trials or phone numbers.
- Never say the reader qualifies. Say "talk to your doctor or the study team".
- Mention that trial details are on ClinicalTrials.gov.
- Friendly, plain language. No medical advice.

## Provider (llm.py)
`generate(prompt) -> str | None`, provider chosen by env vars, never hard-coded keys:
- `LLM_PROVIDER=bedrock` → Amazon Bedrock (boto3 `bedrock-runtime` Converse API), model from `LLM_MODEL`, AWS creds from the normal AWS env vars.
- `LLM_PROVIDER=anthropic` → Anthropic API, key `ANTHROPIC_API_KEY`, model from `LLM_MODEL`.
- Not set / error / 20 s timeout → `None`.
Ask the organizers which provider and key to use. Add only the SDK you actually use to requirements.txt.

## Fallback (must work in the demo)
If `generate` returns None: show `outreach_brief()` text plus `st.caption("AI brief unavailable — showing the standard recommendation.")`.
Cache results per (county, disease, language) in `st.session_state` so repeated clicks don't spend money.

## Optional stretch: "Site Scout" agent (only if time remains after everything else works)
User types a goal ("Where should my next diabetes site go?"). The model calls tools that wrap the
existing deserts.py functions (`county_scores`, `candidate_hospitals`, nearest trials, `ej_summary`),
then returns a recommended county + hospital + reasons + flyer. Show each tool call as a step.
Max 5 tool calls per run.
