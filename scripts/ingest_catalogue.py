"""Task 5/6: loads the raw LTB catalogue CSV into the SQLite orders table,
and normalizes each row's issue codes into the order_issue_codes join table.

Usage:
    .venv/Scripts/python.exe scripts/ingest_catalogue.py
    .venv/Scripts/python.exe scripts/ingest_catalogue.py --csv path/to.csv --db path/to.db

Safely re-runnable: each run drops and recreates the `orders` and
`order_issue_codes` tables (via data/schema.sql) before reloading them, so
the CSV is always the source of truth for the current contents of the DB.
"""

import argparse
import csv
import logging
import re
import sqlite3
import sys
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
SCHEMA_PATH = PROJECT_ROOT / "data" / "schema.sql"
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "ltb.db"

# Required columns (post-cleaning) for a row to be loadable — matches the
# NOT NULL fields in data/schema.sql (city is the only nullable field).
REQUIRED_COLUMNS = ("File Number", "Applications", "Document Type", "Order Date", "View Order")

# The raw "ContentDownload URL" column holds an Excel formula, not a bare
# URL, e.g. =HYPERLINK("https://.../doc.pdf","View file").
VIEW_ORDER_FORMULA_PATTERN = re.compile(r'^=HYPERLINK\("([^"]+)"\s*,\s*"[^"]*"\)$')

logger = logging.getLogger(__name__)


def clean_header(raw_header: str) -> str:
    """Keeps only the text before the "/" in a bilingual "English / French"
    column header, then renames the download-link column per Task 5."""
    name = raw_header.split("/", 1)[0].strip()
    if name == "ContentDownload URL":
        return "View Order"
    return name


def extract_view_order_url(raw_value: str) -> str:
    """Pulls the URL out of the raw column's Excel HYPERLINK formula.

    Falls back to the raw value itself if it isn't wrapped in a formula,
    so a plain URL (e.g. in a hand-written test fixture) still works.
    """
    raw_value = raw_value.strip()
    match = VIEW_ORDER_FORMULA_PATTERN.match(raw_value)
    return match.group(1) if match else raw_value


def split_issue_codes(raw_codes: str) -> List[str]:
    """Parses a raw "T1;T2;T3" field into ["T1", "T2", "T3"] for storage in
    the order_issue_codes join table (Task 6).

    Strips whitespace around each code and drops duplicates within the same
    row (the catalogue has rows like "L1;L1;L1") while preserving order.
    """
    codes: List[str] = []
    for part in raw_codes.split(";"):
        code = part.strip()
        if code and code not in codes:
            codes.append(code)
    return codes


def derive_city(address: str) -> Optional[str]:
    """Derives the city from a "STREET, CITY, PROVINCE POSTALCODE" address.

    The catalogue has no dedicated city column, so this is parsed out of the
    rental unit address. Returns None when the address doesn't have enough
    comma-separated segments to contain a city (e.g. "Multiple Rental Units").
    """
    address = address.strip()
    if not address:
        return None

    parts = [part.strip() for part in address.split(",")]
    if len(parts) < 2:
        return None

    return parts[-2] or None


def _read_rows(csv_path: Path):
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        raw_header = next(csv.reader(f))
        cleaned_header = [clean_header(h) for h in raw_header]
        reader = csv.DictReader(f, fieldnames=cleaned_header)
        yield from reader


def load_catalogue(csv_path: Path, db_path: Path) -> int:
    """Loads `csv_path` into the `orders` table of the SQLite DB at `db_path`.

    Clears and reloads the table on every run. Returns the number of records
    loaded.
    """
    rows_to_insert = []
    skipped = 0

    for row in _read_rows(csv_path):
        file_number = (row.get("File Number") or "").strip()
        issue_codes = (row.get("Applications") or "").strip()
        document_type = (row.get("Document Type") or "").strip()
        order_date = (row.get("Order Date") or "").strip()
        view_order_raw = (row.get("View Order") or "").strip()

        if not (file_number and issue_codes and document_type and order_date and view_order_raw):
            skipped += 1
            logger.warning("Skipping row missing a required field: %s", row)
            continue

        view_order_url = extract_view_order_url(view_order_raw)
        city = derive_city(row.get("Rental Unit Address") or "")

        rows_to_insert.append((file_number, order_date, issue_codes, document_type, city, view_order_url))

    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        cursor = connection.cursor()
        for file_number, order_date, issue_codes, document_type, city, view_order_url in rows_to_insert:
            cursor.execute(
                "INSERT INTO orders (file_number, order_date, issue_codes, document_type, city, view_order_url) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (file_number, order_date, issue_codes, document_type, city, view_order_url),
            )
            order_id = cursor.lastrowid
            cursor.executemany(
                "INSERT INTO order_issue_codes (order_id, code) VALUES (?, ?)",
                [(order_id, code) for code in split_issue_codes(issue_codes)],
            )
        connection.commit()
    finally:
        connection.close()

    logger.info("Loaded %d records into %s (%d skipped)", len(rows_to_insert), db_path, skipped)
    return len(rows_to_insert)


def _find_default_csv(raw_dir: Path) -> Path:
    csv_files = sorted(raw_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV file found in {raw_dir} — see data/raw/README.md to download one")
    return csv_files[0]


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=None, help="raw catalogue CSV (default: first *.csv in data/raw/)")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="SQLite DB to write (default: data/ltb.db)")
    args = parser.parse_args()

    csv_path = args.csv or _find_default_csv(RAW_DATA_DIR)
    count = load_catalogue(csv_path, args.db)
    print(f"Loaded {count} records into {args.db}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
