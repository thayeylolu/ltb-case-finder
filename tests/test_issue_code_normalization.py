"""Task 6: verifies issue-code normalization in the ingestion pipeline."""

import csv
import sqlite3
from pathlib import Path

import pytest

from scripts.ingest_catalogue import load_catalogue, split_issue_codes

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "data" / "schema.sql"

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


@pytest.fixture()
def conn():
    connection = sqlite3.connect(":memory:")
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    yield connection
    connection.close()


def test_split_issue_codes_parses_multiple_codes():
    assert split_issue_codes("T1;T2;T3") == ["T1", "T2", "T3"]


def test_split_issue_codes_handles_a_single_code():
    assert split_issue_codes("C2") == ["C2"]


def test_split_issue_codes_dedupes_repeated_codes_in_one_row():
    assert split_issue_codes("L1;L1;L1") == ["L1"]


def test_split_issue_codes_strips_whitespace():
    assert split_issue_codes(" T1 ; T2 ") == ["T1", "T2"]


def test_order_issue_codes_table_has_expected_columns(conn):
    columns = {row[1] for row in conn.execute("PRAGMA table_info(order_issue_codes)").fetchall()}
    assert columns == {"order_id", "code"}


def test_order_issue_codes_code_index_exists(conn):
    indexes = {row[1] for row in conn.execute("PRAGMA index_list(order_issue_codes)").fetchall()}
    assert "idx_order_issue_codes_code" in indexes


def test_load_catalogue_explodes_a_multi_code_row_into_the_join_table(tmp_path):
    csv_path = _write_csv(
        tmp_path / "catalogue.csv",
        [
            [
                "1",
                "LTB-C-001226-26",
                "T1;T2;T3",
                "",
                "8-48 CAROGA CRT, HAMILTON, ON L9C7M4",
                "Order",
                "2026-04-01",
                '=HYPERLINK("https://example.com/doc1.pdf","View file")',
            ],
        ],
    )
    db_path = tmp_path / "ltb.db"

    load_catalogue(csv_path, db_path)

    conn = sqlite3.connect(db_path)
    order_id = conn.execute("SELECT id FROM orders WHERE file_number = 'LTB-C-001226-26'").fetchone()[0]
    codes = sorted(
        row[0] for row in conn.execute("SELECT code FROM order_issue_codes WHERE order_id = ?", (order_id,))
    )
    total_rows = conn.execute("SELECT COUNT(*) FROM order_issue_codes").fetchone()[0]
    conn.close()

    assert codes == ["T1", "T2", "T3"]
    assert total_rows == 3


def test_load_catalogue_links_codes_to_the_correct_order_when_multiple_orders_exist(tmp_path):
    csv_path = _write_csv(
        tmp_path / "catalogue.csv",
        [
            [
                "1",
                "LTB-C-000798-26",
                "C2",
                "",
                "1002-111 BELMONT DR, LONDON, ON N6J4X9",
                "Order",
                "2026-03-12",
                '=HYPERLINK("https://example.com/doc1.pdf","View file")',
            ],
            [
                "2",
                "LTB-C-001226-26",
                "C4;T2",
                "",
                "8-48 CAROGA CRT, HAMILTON, ON L9C7M4",
                "Order",
                "2026-04-01",
                '=HYPERLINK("https://example.com/doc2.pdf","View file")',
            ],
        ],
    )
    db_path = tmp_path / "ltb.db"

    loaded = load_catalogue(csv_path, db_path)
    assert loaded == 2

    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT orders.file_number, order_issue_codes.code "
        "FROM order_issue_codes JOIN orders ON orders.id = order_issue_codes.order_id "
        "ORDER BY orders.file_number, order_issue_codes.code"
    ).fetchall()
    conn.close()

    assert rows == [
        ("LTB-C-000798-26", "C2"),
        ("LTB-C-001226-26", "C4"),
        ("LTB-C-001226-26", "T2"),
    ]


def test_load_catalogue_is_safely_rerunnable_for_the_join_table(tmp_path):
    csv_path = _write_csv(
        tmp_path / "catalogue.csv",
        [
            [
                "1",
                "LTB-C-001226-26",
                "T1;T2",
                "",
                "8-48 CAROGA CRT, HAMILTON, ON L9C7M4",
                "Order",
                "2026-04-01",
                '=HYPERLINK("https://example.com/doc1.pdf","View file")',
            ],
        ],
    )
    db_path = tmp_path / "ltb.db"

    load_catalogue(csv_path, db_path)
    load_catalogue(csv_path, db_path)

    conn = sqlite3.connect(db_path)
    total_rows = conn.execute("SELECT COUNT(*) FROM order_issue_codes").fetchone()[0]
    conn.close()

    assert total_rows == 2, "re-running ingestion should clear and reload the join table, not duplicate rows"
