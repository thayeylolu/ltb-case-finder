"""Runs the full pytest suite and appends a row to docs/mvp0/test_log.md.

Usage:
    .venv/Scripts/python.exe scripts/log_test_run.py --task "4. SQLite Database Schema" --files tests/test_schema.py

See CLAUDE.md "Testing" for why this log exists and when to run it.
"""

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_LOG_PATH = PROJECT_ROOT / "docs" / "mvp0" / "test_log.md"

SUMMARY_LINE_PATTERN = re.compile(r"^=+ .* in [\d.]+s ?=*$", re.MULTILINE)
COLLECTED_PATTERN = re.compile(r"collected (\d+) item")
OUTCOME_PATTERN = re.compile(r"(\d+) (passed|failed|error|errors|skipped|xfailed|xpassed)")


def parse_pytest_output(output: str) -> dict:
    """Extracts collected/passed/failed/etc counts from `pytest -v` stdout."""
    collected_match = COLLECTED_PATTERN.search(output)
    collected = int(collected_match.group(1)) if collected_match else 0

    summary_match = SUMMARY_LINE_PATTERN.search(output)
    summary_line = summary_match.group(0) if summary_match else ""

    counts = {"passed": 0, "failed": 0, "error": 0, "skipped": 0, "xfailed": 0, "xpassed": 0}
    for count, outcome in OUTCOME_PATTERN.findall(summary_line):
        key = "error" if outcome == "errors" else outcome
        counts[key] = int(count)

    return {"collected": collected, "summary_line": summary_line, **counts}


def format_result(counts: dict) -> str:
    """e.g. '19/19 passed' or '17/19 passed (2 failed)'."""
    result = f"{counts['passed']}/{counts['collected']} passed"

    trouble = []
    for key in ("failed", "error", "skipped"):
        if counts[key]:
            label = "errored" if key == "error" else key
            trouble.append(f"{counts[key]} {label}")
    if trouble:
        result += f" ({', '.join(trouble)})"

    return result


def append_row(task: str, files: str, counts: dict, notes: str) -> None:
    result = format_result(counts)
    row = f"| {task} | {date.today().isoformat()} | `{files}` | {result} | {notes} |\n"

    content = TEST_LOG_PATH.read_text(encoding="utf-8")
    TEST_LOG_PATH.write_text(content.rstrip("\n") + "\n" + row, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, help='e.g. "4. SQLite Database Schema"')
    parser.add_argument("--files", required=True, help="test file(s) added/changed for this task")
    parser.add_argument("--notes", default="", help="extra notes for the log row")
    parser.add_argument("--dry-run", action="store_true", help="print the row instead of writing it")
    args = parser.parse_args()

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-v"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    print(proc.stdout)
    print(proc.stderr, file=sys.stderr)

    counts = parse_pytest_output(proc.stdout)
    notes = args.notes
    if counts["failed"] or counts["error"]:
        notes = (notes + " " if notes else "") + "SEE FAILURE OUTPUT ABOVE."

    if args.dry_run:
        print(f"[dry-run] {args.task} | {date.today().isoformat()} | {args.files} | {format_result(counts)} | {notes}")
    else:
        append_row(args.task, args.files, counts, notes)
        print(f"Logged to {TEST_LOG_PATH.relative_to(PROJECT_ROOT)}: {format_result(counts)}")

    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
