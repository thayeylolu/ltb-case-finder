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
