"""Task 5: verifies the catalogue ingestion script (scripts/ingest_catalogue.py)."""

import csv
import sqlite3

import pytest

from scripts.ingest_catalogue import (
    clean_header,
    derive_city,
    extract_view_order_url,
    load_catalogue,
)

# Mirrors the real raw catalogue header shape: bilingual "English / French"
# names, and a duplicate "Rental Unit Address" column pair where the first
# is often blank and the second (later) one carries the real address.
RAW_HEADER = [
    "_id",
    "File Number/Numéro de dossier",
    "Applications/Requêtes",
    "Rental Unit Address//Adresse du logement locatif",
    "Rental Unit Address/Adresse du logement locatif",
    "Document Type/Type de document",
    "Order Date/Date de l'ordonnance",
    "ContentDownload URL/URL de téléchargement du contenu",
]


def _write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(RAW_HEADER)
        writer.writerows(rows)
    return path


def test_clean_header_keeps_only_text_before_slash():
    assert clean_header("File Number/Numéro de dossier") == "File Number"
    assert clean_header("Applications/Requêtes") == "Applications"


def test_clean_header_renames_content_download_url_to_view_order():
    assert clean_header("ContentDownload URL/URL de téléchargement du contenu") == "View Order"


def test_extract_view_order_url_from_excel_hyperlink_formula():
    raw = '=HYPERLINK("https://example.com/doc1.pdf","View file")'
    assert extract_view_order_url(raw) == "https://example.com/doc1.pdf"


def test_extract_view_order_url_falls_back_to_raw_value():
    assert extract_view_order_url("https://example.com/doc1.pdf") == "https://example.com/doc1.pdf"


def test_derive_city_from_standard_address():
    assert derive_city("8-48 CAROGA CRT, HAMILTON, ON L9C7M4") == "HAMILTON"


def test_derive_city_returns_none_when_no_city_segment():
    assert derive_city("Multiple Rental Units/Plusieurs unités de location") is None


def test_derive_city_returns_none_for_empty_address():
    assert derive_city("") is None


def test_load_catalogue_inserts_expected_rows_using_the_data_bearing_duplicate_column(tmp_path):
    csv_path = _write_csv(
        tmp_path / "catalogue.csv",
        [
            [
                "1",
                "LTB-C-001226-26",
                "T1;T2;T3",
                "",  # blank duplicate "Rental Unit Address" column
                "8-48 CAROGA CRT, HAMILTON, ON L9C7M4",
                "Order",
                "2026-04-01",
                '=HYPERLINK("https://example.com/doc1.pdf","View file")',
            ],
        ],
    )
    db_path = tmp_path / "ltb.db"

    loaded = load_catalogue(csv_path, db_path)
    assert loaded == 1

    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT file_number, order_date, issue_codes, document_type, city, view_order_url FROM orders"
    ).fetchone()
    conn.close()

    assert row == (
        "LTB-C-001226-26",
        "2026-04-01",
        "T1;T2;T3",
        "Order",
        "HAMILTON",
        "https://example.com/doc1.pdf",
    )


def test_load_catalogue_skips_rows_missing_a_required_field(tmp_path):
    csv_path = _write_csv(
        tmp_path / "catalogue.csv",
        [
            [
                "1",
                "",  # missing File Number
                "T1",
                "",
                "123 MAIN ST, LONDON, ON N6J4X9",
                "Order",
                "2026-01-01",
                '=HYPERLINK("https://example.com/doc1.pdf","View file")',
            ],
            [
                "2",
                "LTB-C-000798-26",
                "C2",
                "",
                "123 MAIN ST, LONDON, ON N6J4X9",
                "Order",
                "2026-01-02",
                '=HYPERLINK("https://example.com/doc2.pdf","View file")',
            ],
        ],
    )
    db_path = tmp_path / "ltb.db"

    loaded = load_catalogue(csv_path, db_path)
    assert loaded == 1

    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    conn.close()
    assert count == 1


def test_load_catalogue_is_safely_rerunnable(tmp_path):
    csv_path = _write_csv(
        tmp_path / "catalogue.csv",
        [
            [
                "1",
                "LTB-C-001226-26",
                "C4",
                "",
                "8-48 CAROGA CRT, HAMILTON, ON L9C7M4",
                "Order",
                "2026-04-01",
                '=HYPERLINK("https://example.com/doc1.pdf","View file")',
            ],
        ],
    )
    db_path = tmp_path / "ltb.db"

    first_run = load_catalogue(csv_path, db_path)
    second_run = load_catalogue(csv_path, db_path)

    assert first_run == 1
    assert second_run == 1

    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    conn.close()
    assert count == 1, "re-running ingestion should clear and reload, not duplicate rows"
