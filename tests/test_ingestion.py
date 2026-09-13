"""Task 5: verifies the catalogue ingestion script (scripts/ingest_catalogue.py)."""

import csv
import sqlite3

import pytest

from scripts.ingest_catalogue import (
    clean_header,
    derive_city,
    derive_resident_type_and_address,
    extract_view_order_url,
    load_catalogue,
    merge_rental_unit_address,
)

# Mirrors the real raw catalogue header shape: bilingual "English / French"
# names, a "Complex Address" column, and a duplicate "Rental Unit Address"
# column pair straddling it — only one of the pair is ever populated per
# row, and it isn't always the same one.
RAW_HEADER = [
    "_id",
    "File Number/Numéro de dossier",
    "Applications/Requêtes",
    "Rental Unit Address//Adresse du logement locatif",
    "Complex Address/Adresse du complexe",
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


def _row(file_number, issue_codes, rental_1, complex_address, rental_2, order_date, doc_id):
    return [
        doc_id,
        file_number,
        issue_codes,
        rental_1,
        complex_address,
        rental_2,
        "Order",
        order_date,
        f'=HYPERLINK("https://example.com/{doc_id}.pdf","View file")',
    ]


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


def test_derive_city_from_a_complex_address_with_province_in_its_own_segment():
    # Complex Address values put the province and postal code in separate
    # comma segments ("STREET, CITY, PROVINCE, POSTALCODE"), unlike the
    # merged rental unit address's "STREET, CITY, PROVINCE POSTALCODE".
    assert derive_city("815 Kennedy Road, Scarborough, Ontario, M1K 2E3") == "Scarborough"


def test_merge_rental_unit_address_prefers_the_preferred_column_when_populated():
    assert merge_rental_unit_address("8-48 CAROGA CRT, HAMILTON, ON L9C7M4", "") == "8-48 CAROGA CRT, HAMILTON, ON L9C7M4"


def test_merge_rental_unit_address_falls_back_when_preferred_is_blank():
    assert merge_rental_unit_address("", "8-48 CAROGA CRT, HAMILTON, ON L9C7M4") == "8-48 CAROGA CRT, HAMILTON, ON L9C7M4"


def test_merge_rental_unit_address_prefers_the_preferred_column_even_when_both_are_populated():
    # Real catalogue rows have both duplicate columns populated on almost
    # every row, with the first ("fallback" here) using a less parseable
    # format — e.g. an extra comma before the postal code — than the
    # second ("preferred"). Confirms `preferred` always wins, not just
    # when `fallback` happens to be blank.
    assert (
        merge_rental_unit_address(
            "Upper Unit-203 Pellatt Avenue, Northyork, ON M9N2P5",
            "Upper Unit, 203 Pellatt Avenue, Northyork, ON, M9N2P5",
        )
        == "Upper Unit-203 Pellatt Avenue, Northyork, ON M9N2P5"
    )


def test_merge_rental_unit_address_returns_empty_when_both_are_empty():
    assert merge_rental_unit_address("", "") == ""


def test_derive_resident_type_and_address_from_rental_unit_only():
    assert derive_resident_type_and_address("8-48 CAROGA CRT, HAMILTON, ON L9C7M4", "") == (
        "Rental Unit",
        "8-48 CAROGA CRT, HAMILTON, ON L9C7M4",
    )


def test_derive_resident_type_and_address_from_complex_only():
    assert derive_resident_type_and_address("", "100 MAIN ST, LONDON, ON N6J4X9") == (
        "Complex",
        "100 MAIN ST, LONDON, ON N6J4X9",
    )


def test_derive_resident_type_and_address_prefers_complex_when_both_are_present():
    assert derive_resident_type_and_address(
        "8-48 CAROGA CRT, HAMILTON, ON L9C7M4", "100 MAIN ST, LONDON, ON N6J4X9"
    ) == ("Complex", "100 MAIN ST, LONDON, ON N6J4X9")


def test_derive_resident_type_and_address_returns_empty_when_neither_is_given():
    assert derive_resident_type_and_address("", "") == ("", "")


def _loaded_row(db_path):
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT file_number, order_date, issue_codes, document_type, city, resident_type, address, "
        "view_order_url FROM orders"
    ).fetchone()
    conn.close()
    return row


def test_load_catalogue_uses_the_first_rental_unit_address_column_when_the_second_is_blank(tmp_path):
    # Regression test: this used to fail because both duplicate "Rental Unit
    # Address" columns cleaned to the same name, and csv.DictReader silently
    # kept only the *last* column's value — discarding the first even when
    # it was the one that actually had data.
    csv_path = _write_csv(
        tmp_path / "catalogue.csv",
        [_row("LTB-C-001226-26", "T1;T2;T3", "8-48 CAROGA CRT, HAMILTON, ON L9C7M4", "", "", "2026-04-01", "1")],
    )
    db_path = tmp_path / "ltb.db"

    loaded = load_catalogue(csv_path, db_path)
    assert loaded == 1
    assert _loaded_row(db_path) == (
        "LTB-C-001226-26",
        "2026-04-01",
        "T1;T2;T3",
        "Order",
        "HAMILTON",
        "Rental Unit",
        "8-48 CAROGA CRT, HAMILTON, ON L9C7M4",
        "https://example.com/1.pdf",
    )


def test_load_catalogue_uses_the_second_rental_unit_address_column_when_the_first_is_blank(tmp_path):
    csv_path = _write_csv(
        tmp_path / "catalogue.csv",
        [_row("LTB-C-001226-26", "T1;T2;T3", "", "", "8-48 CAROGA CRT, HAMILTON, ON L9C7M4", "2026-04-01", "1")],
    )
    db_path = tmp_path / "ltb.db"

    loaded = load_catalogue(csv_path, db_path)
    assert loaded == 1
    assert _loaded_row(db_path) == (
        "LTB-C-001226-26",
        "2026-04-01",
        "T1;T2;T3",
        "Order",
        "HAMILTON",
        "Rental Unit",
        "8-48 CAROGA CRT, HAMILTON, ON L9C7M4",
        "https://example.com/1.pdf",
    )


def test_load_catalogue_prefers_the_second_rental_unit_address_column_when_both_are_populated(tmp_path):
    # Regression test for the real catalogue shape: both duplicate columns
    # are populated on almost every row, and the first one's extra comma
    # before the postal code (e.g. "..., Northyork, ON, M9N2P5") breaks
    # derive_city's parsing if it's the one used — the second column's
    # single-comma format (e.g. "..., Northyork, ON M9N2P5") is the one
    # that must win.
    csv_path = _write_csv(
        tmp_path / "catalogue.csv",
        [
            _row(
                "LTB-L-000003-26",
                "L1",
                "Upper Unit, 203 Pellatt Avenue, Northyork, ON, M9N2P5",
                "",
                "Upper Unit-203 Pellatt Avenue, Northyork, ON M9N2P5",
                "2026-01-05",
                "5",
            )
        ],
    )
    db_path = tmp_path / "ltb.db"

    loaded = load_catalogue(csv_path, db_path)
    assert loaded == 1
    row = _loaded_row(db_path)
    assert row[4] == "Northyork"  # city
    assert row[6] == "Upper Unit-203 Pellatt Avenue, Northyork, ON M9N2P5"  # address


def test_load_catalogue_uses_complex_address_when_no_rental_unit_address_is_given(tmp_path):
    csv_path = _write_csv(
        tmp_path / "catalogue.csv",
        [_row("LTB-C-000798-26", "C2", "", "100 MAIN ST, LONDON, ON N6J4X9", "", "2026-01-02", "2")],
    )
    db_path = tmp_path / "ltb.db"

    loaded = load_catalogue(csv_path, db_path)
    assert loaded == 1
    assert _loaded_row(db_path) == (
        "LTB-C-000798-26",
        "2026-01-02",
        "C2",
        "Order",
        "LONDON",
        "Complex",
        "100 MAIN ST, LONDON, ON N6J4X9",
        "https://example.com/2.pdf",
    )


def test_load_catalogue_derives_city_from_a_complex_address_correctly(tmp_path):
    # Regression test: the raw Complex Address column always has the
    # 4-segment "STREET, CITY, PROVINCE, POSTALCODE" shape, which used to
    # make derive_city return "Ontario" instead of the actual city.
    csv_path = _write_csv(
        tmp_path / "catalogue.csv",
        [_row("LTB-C-000900-26", "C2", "", "815 Kennedy Road, Scarborough, Ontario, M1K 2E3", "", "2026-01-04", "4")],
    )
    db_path = tmp_path / "ltb.db"

    loaded = load_catalogue(csv_path, db_path)
    assert loaded == 1
    row = _loaded_row(db_path)
    assert row[4] == "Scarborough"  # city
    assert row[5] == "Complex"  # resident_type


def test_load_catalogue_leaves_resident_type_and_address_empty_when_neither_is_given(tmp_path):
    csv_path = _write_csv(
        tmp_path / "catalogue.csv",
        [_row("LTB-C-000799-26", "C2", "", "", "", "2026-01-03", "3")],
    )
    db_path = tmp_path / "ltb.db"

    loaded = load_catalogue(csv_path, db_path)
    assert loaded == 1
    row = _loaded_row(db_path)
    assert row[4] is None  # city
    assert row[5] == ""  # resident_type
    assert row[6] == ""  # address


def test_load_catalogue_skips_rows_missing_a_required_field(tmp_path):
    csv_path = _write_csv(
        tmp_path / "catalogue.csv",
        [
            _row("", "T1", "", "", "123 MAIN ST, LONDON, ON N6J4X9", "2026-01-01", "1"),  # missing File Number
            _row("LTB-C-000798-26", "C2", "", "", "123 MAIN ST, LONDON, ON N6J4X9", "2026-01-02", "2"),
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
        [_row("LTB-C-001226-26", "C4", "", "", "8-48 CAROGA CRT, HAMILTON, ON L9C7M4", "2026-04-01", "1")],
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
