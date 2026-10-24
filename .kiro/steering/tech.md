# Tech

- Python 3.14 in .venv/. Libraries: requests, truststore, pandas, numpy, streamlit, plotly, pytest, hypothesis.
- Map: Plotly go.Choroplethmap + go.Scattermap (map_style "carto-positron"). Do not use pydeck or altair.
- Call truststore.inject_into_ssl() (in try/except ImportError) before HTTP requests; fixes Mac SSL errors.
- Record dependencies in requirements.txt.
- Simple, readable code, short comments, no over-engineering.

## Working rules (save credits)
- Never open or read files in data/ (large JSON). Use the schemas in docs/03-data-sources.md.
- Do not run long-running commands (streamlit run, fetch_data.py); the user runs them in the terminal.
- Make the smallest change that completes the task. Do not refactor unrelated code.
- Never run git commit or git push. The two team members commit themselves so authorship is correct.
