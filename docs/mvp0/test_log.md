# MVP 0 Test Log

A run-by-run record of the full test suite (`.venv/Scripts/python.exe -m pytest -v`), logged after each task that adds or changes tests. Purpose: when a later run fails, scan backwards to find the last task where the suite was green and narrow down which task's change broke it. Documentation-only tasks (no functional code change, e.g. a `.md` edit) are not logged here — see `CLAUDE.md` "Testing".

`Full suite result` is always written as `passed/collected` (e.g. `19/19`) so it's unambiguous at a glance — never just a bare count — and any failed/errored/skipped tests are called out explicitly in Notes rather than left implicit.

| Task | Date | Test file(s) | Full suite result | Notes |
| --- | --- | --- | --- | --- |
| 1. Project Setup | 2026-09-13 | `tests/test_project_setup.py` | 3/3 passed | Verified at commit `bd766a3` (checked out and re-run). |
| 2. Acquire Catalogue Snapshot | 2026-09-13 | `tests/test_data_acquisition.py` | 6/6 passed | Verified at commit `11c0f6e` (checked out and re-run). |
| 3. Issue Taxonomy Mapping | 2026-09-13 | `tests/test_issue_taxonomy.py` | 13/13 passed | Verified at commit `7bcbff0` (checked out and re-run). |
| 4. SQLite Database Schema | 2026-09-13 | `tests/test_schema.py` | 19/19 passed | Run on working tree before commit; no failures, errors, or skips. |
| Tooling: automate test log | 2026-09-13 | `scripts/log_test_run.py, tests/test_log_test_run_script.py` | 25/25 passed | Adds the script itself; row appended by running it, not by hand. |
| 5. Catalogue Ingestion Script | 2026-09-13 | `tests/test_ingestion.py` | 35/35 passed |  |
| 6. Issue Code Normalization | 2026-09-13 | `tests/test_issue_code_normalization.py` | 44/44 passed |  |
| 7. FastAPI Application Skeleton | 2026-09-13 | `tests/test_health.py` | 46/46 passed |  |
| 8. Issue-to-Code Lookup Service | 2026-09-13 | `tests/test_taxonomy_lookup.py` | 51/51 passed |  |
| 9. Case Filtering Query | 2026-09-13 | `tests/test_case_filtering.py` | 58/58 passed |  |
| 10. Result Ranking and Limiting Logic | 2026-09-13 | `tests/test_ranking.py` | 64/64 passed |  |
| 11. POST /search API Endpoint | 2026-09-13 | `tests/test_search_endpoint.py` | 70/70 passed |  |
| 12. Frontend Issue Selection UI | 2026-09-13 | `tests/test_frontend_issue_selection.py` | 75/75 passed | Also manually verified in Chrome via a local static server: all 14 checkboxes render, styling applied, checkbox toggling confirmed. |
| 12. Frontend Issue Selection UI (alphabetical order fix) | 2026-09-13 | `tests/test_frontend_issue_selection.py` | 76/76 passed | User feedback: sort issue checkboxes alphabetically. Re-verified visually in Chrome. |
| 13. Frontend Search Submission and API Integration | 2026-09-13 | `tests/test_frontend_search_integration.py` | 84/84 passed | Manually verified end-to-end in Chrome: backend on 127.0.0.1:8000 (CORS enabled), frontend served via local static server on a different port; selecting Maintenance and clicking Search logged 20 results to console, and clicking Search with nothing selected logged a warning without a network call. |
| 14. Results Table Rendering | 2026-09-13 | `tests/test_frontend_results_table.py` | 89/89 passed | Manually verified in Chrome: table renders with all 6 columns, issues joined with the plan.md separator, View Order links open in a new tab with rel=noopener, capped at 20 rows, and renderResults([]) clears the container without error. |
