"""Task 2: verifies the raw LTB catalogue snapshot and its source documentation."""

import csv
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
README_PATH = RAW_DATA_DIR / "README.md"

EXPECTED_SOURCE_URL = "https://data.ontario.ca/datastore/dump/86e75d11-1c2c-4cd9-9b0d-9fccec302b30"

# Bilingual "English / French" column headers the ingestion pipeline (Task 5)
# will depend on being present in the raw download.
REQUIRED_COLUMN_PREFIXES = [
    "File Number",
    "Applications",
    "Order Date",
    "Document Type",
    "ContentDownload URL",
]


def _find_raw_csv():
    csv_files = list(RAW_DATA_DIR.glob("*.csv"))
    return csv_files[0] if csv_files else None


def test_raw_data_readme_documents_source():
    assert README_PATH.exists(), "data/raw/README.md is missing — Task 2 requires documenting the source"

    content = README_PATH.read_text(encoding="utf-8")
    assert EXPECTED_SOURCE_URL in content, "README does not document the expected Ontario Open Data source URL"
    assert "download" in content.lower() and any(char.isdigit() for char in content), (
        "README should record a download date"
    )
    assert "csv" in content.lower(), "README should document the file format"


def test_raw_snapshot_present_and_has_expected_columns():
    csv_path = _find_raw_csv()
    if csv_path is None:
        pytest.skip(
            "No CSV found in data/raw/ — it's gitignored and must be downloaded locally "
            "(see data/raw/README.md for the reproduction command)."
        )

    assert csv_path.stat().st_size > 0, f"{csv_path.name} is empty"

    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        header = next(csv.reader(f))

    for expected_prefix in REQUIRED_COLUMN_PREFIXES:
        assert any(col.startswith(expected_prefix) for col in header), (
            f"Expected a column starting with '{expected_prefix}' in {csv_path.name}, got: {header}"
        )


def test_raw_snapshot_has_data_rows():
    csv_path = _find_raw_csv()
    if csv_path is None:
        pytest.skip("No CSV found in data/raw/ — see data/raw/README.md to download it locally.")

    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader)  # header
        first_data_row = next(reader, None)

    assert first_data_row is not None, f"{csv_path.name} has a header but no data rows"
