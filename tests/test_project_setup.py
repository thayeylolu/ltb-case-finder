"""Task 1: verifies the project skeleton and test runner are wired up correctly."""

import importlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_pytest_runs():
    assert 1 + 1 == 2


def test_expected_top_level_folders_exist():
    for folder in ("backend", "frontend", "data", "tests", "config", "docs"):
        assert (PROJECT_ROOT / folder).is_dir(), f"missing expected folder: {folder}"


def test_backend_package_is_importable():
    module = importlib.import_module("backend")
    assert module is not None
