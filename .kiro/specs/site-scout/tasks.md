# Implementation Plan: Site Scout

## Part A: What-if simulator (author Karuniya, branch feature/what-if-simulator)

- [x] 1. `deserts.py`: split `county_scores`, add `simulate_new_site`
  - _Requirements: 1.1 to 1.4_
- [x] 2. `app.py`: hospital picker, "Simulate a new trial site here", before/after result
  - _Requirements: 1.5, 1.6_
- [x] 3. Tests: property P6 and a unit test for the before/after columns
  - _Requirements: 1.2 to 1.4_
- [x] 4. Run `pytest -q`
- [x] 5. Git: commit, push, PR, merge

## Part B: Site Scout agent (author Dheepak, branch feature/site-scout-agent, after A is merged)

- [ ] 6. `llm.py`: `chat_with_tools`
  - _Requirements: 2.1_
- [ ] 7. `scout.py`: tools, agent loop, offline fallback
  - _Requirements: 2.2 to 2.5, 3.1, 3.2_
- [ ] 8. `app.py`: Site Scout tab
  - _Requirements: 4.1 to 4.3_
- [ ] 9. Tests: fallback picks worst county; tools are JSON-serializable
- [ ] 10. Run `pytest -q`
- [ ] 11. Git: commit, push, PR, merge
