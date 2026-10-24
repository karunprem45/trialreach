# Structure (flat)

```
fetch_data.py    downloads all datasets into data/
deserts.py       pure scoring functions (pandas/numpy, no Streamlit)
llm.py           one optional LLM call with a safe fallback
app.py           Streamlit UI only
tests/           pytest + hypothesis tests
data/            saved JSON, COMMITTED to git so the app runs offline for judges
docs/            planning docs (PRD, design, data, UI, AI, tests, build plan)
```
- Keep logic in deserts.py so it is testable; app.py only displays.
- Never commit .venv/, __pycache__/, .pytest_cache/, or API keys.
