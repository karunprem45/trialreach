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

## Git workflow (company style)
- Never commit directly to main. One branch per feature: feature/<name>, fix/<name>, docs/<name>.
- Before each commit, set the author with `bash scripts/as-karuniya.sh` or `bash scripts/as-dheepak.sh` (the owner of that work).
- Conventional commit messages: feat:, fix:, test:, docs:, chore:.
- Push the branch, open a PR with `gh pr create --base main`, then merge with `gh pr merge --merge --delete-branch` (merge commits keep each author).
- Never force-push, never rewrite history, never commit .venv/, caches or API keys.
