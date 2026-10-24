---
inclusion: manual
description: "Manual checklist to run before each push"
---

Check, without editing files: (1) `git config user.name` and show it, (2) no API keys or tokens in tracked files, (3) `.kiro/` is not in .gitignore, (4) requirements.txt lists every imported third-party package, (5) `python -m pytest -q` passes. Reply with a 5-line checklist.
