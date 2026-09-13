"""Tests for scripts/log_test_run.py's pytest-output parsing (not a task from tasks.md;
tooling added to support the test-log workflow described in CLAUDE.md "Testing")."""

from scripts.log_test_run import format_result, parse_pytest_output

ALL_PASSED_OUTPUT = """
collecting ... collected 19 items

tests/test_schema.py::test_schema_file_exists PASSED                     [100%]

============================= 19 passed in 0.05s ==============================
"""

WITH_FAILURES_OUTPUT = """
collecting ... collected 19 items

tests/test_schema.py::test_schema_file_exists FAILED                     [100%]

=================================== FAILURES ===================================
...
========================= 2 failed, 17 passed in 0.12s =========================
"""

WITH_SKIPS_OUTPUT = """
collecting ... collected 6 items

tests/test_data_acquisition.py::test_raw_snapshot_present_and_has_expected_columns SKIPPED [100%]

=================== 5 passed, 1 skipped in 0.03s ====================
"""


def test_parses_all_passed():
    counts = parse_pytest_output(ALL_PASSED_OUTPUT)
    assert counts["collected"] == 19
    assert counts["passed"] == 19
    assert counts["failed"] == 0


def test_parses_failures():
    counts = parse_pytest_output(WITH_FAILURES_OUTPUT)
    assert counts["collected"] == 19
    assert counts["passed"] == 17
    assert counts["failed"] == 2


def test_parses_skips():
    counts = parse_pytest_output(WITH_SKIPS_OUTPUT)
    assert counts["collected"] == 6
    assert counts["passed"] == 5
    assert counts["skipped"] == 1


def test_format_result_all_passed():
    counts = parse_pytest_output(ALL_PASSED_OUTPUT)
    assert format_result(counts) == "19/19 passed"


def test_format_result_with_failures():
    counts = parse_pytest_output(WITH_FAILURES_OUTPUT)
    assert format_result(counts) == "17/19 passed (2 failed)"


def test_format_result_with_skips():
    counts = parse_pytest_output(WITH_SKIPS_OUTPUT)
    assert format_result(counts) == "5/6 passed (1 skipped)"
