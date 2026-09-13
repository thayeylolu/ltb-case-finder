# CLAUDE.md

Project conventions for LTB Case Finder. Read `docs/mvp0/plan.md` (spec), `docs/mvp0/tasks.md` (task backlog), and `docs/mvp0/architecture.md` (component design) for full context — this file only covers working conventions.

## Branching

* All MVP 0 work happens on the `mvp0` branch. `main` stays untouched until MVP 0 is complete and ready to be merged in.
* GitHub repo: `thayeylolu/ltb-case-finder` (public).

## Commit messages

Use Conventional Commits style: `type(scope): summary`, with a body explaining *why*, not just what.

* `docs:` — changes to `docs/`, `README.md`, or other documentation
* `feat:` — new user-facing functionality
* `fix:` — bug fixes
* `chore:` — tooling, dependencies, project setup (e.g. `chore(setup): ...`)
* `test:` — test-only changes

When a commit completes a task from `docs/mvp0/tasks.md`, reference the matching GitHub issue (issue numbers match task numbers 1:1, e.g. Task 1 = issue #1) with `Closes #N` or `Refs #N`.

Keep unrelated changes in separate commits (e.g. doc fixes and a task implementation are two commits, not one).

## GitHub issues

Every task backlog issue must be tagged with a label naming the MVP milestone it belongs to (e.g. `mvp0`). When starting a new milestone's task backlog (MVP 1, MVP 2, ...), create the matching label first (`gh label create "mvp1" ...`) and apply it to every issue created for that milestone's tasks.

## Source of truth locations

* **Issue taxonomy** (user-facing category name ↔ official LTB application code): `config/issue_taxonomy.json`. This is authoritative — don't hardcode category/code mappings elsewhere.
* **Raw catalogue data**: `data/raw/`. Reproducible from the Ontario Open Data source documented in `data/raw/README.md` — never commit the CSV itself, only the README describing how to regenerate it.
* **Task backlog**: `docs/mvp0/tasks.md`. If tasks are reordered or reworded, check for stale cross-references to other task numbers elsewhere in the same file and in `docs/mvp0/architecture.md`.

## Data handling rules

* Never commit raw catalogue CSVs or the generated SQLite database (`*.db`) — both are gitignored and regenerated locally.
* Never commit `eda.ipynb` with cell outputs intact — the raw catalogue contains real tenant/landlord/co-op member names and addresses in its rows, and notebook outputs can bake those into the repo even though the source dataset itself is public. It's gitignored; if it needs to be shared, strip outputs first.
* Raw catalogue CSV columns are bilingual (`English / French`); the ingestion pipeline keeps only the text before the `/`. The `ContentDownload URL` column is renamed to `View Order`.

## Testing

* Every task must include tests, not just the implementation, unless the task is purely documentation (e.g. creating or editing a `.md` file with no functional code change) — those don't need a test.
* If a task's own description doesn't call out a test explicitly, still add one covering the new behavior before considering the task done.
* After adding a task's tests, log the run with `.venv/Scripts/python.exe scripts/log_test_run.py --task "<task>" --files "<test file(s)>"` instead of running pytest and editing `docs/mvp0/test_log.md` by hand. The script runs the **full** suite (not just the new file — this catches a new task regressing something an earlier task's tests already covered), parses the pytest summary, and appends a row itself, so the logged `passed/collected` count (e.g. `19/19`) always matches what actually ran. Use `--dry-run` to preview the row without writing it, and `--notes` for anything worth calling out.

## Local dev environment

* Python virtual environment: `.venv/` (gitignored). Dependencies in `requirements.txt`.
* Run tests: `.venv/Scripts/python.exe -m pytest -v` (or activate the venv first, then `pytest -v`).
