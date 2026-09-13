"""Task 4: verifies the SQLite schema (data/schema.sql)."""

import sqlite3
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "data" / "schema.sql"

# column -> (type, notnull)
EXPECTED_COLUMNS = {
    "id": ("INTEGER", 0),
    "file_number": ("TEXT", 1),
    "order_date": ("TEXT", 1),
    "issue_codes": ("TEXT", 1),
    "document_type": ("TEXT", 1),
    "city": ("TEXT", 0),
    "view_order_url": ("TEXT", 1),
}


@pytest.fixture()
def conn():
    connection = sqlite3.connect(":memory:")
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    yield connection
    connection.close()


def test_schema_file_exists():
    assert SCHEMA_PATH.exists(), "data/schema.sql is missing"


def test_orders_table_has_expected_columns(conn):
    columns = {
        row[1]: (row[2], row[3])
        for row in conn.execute("PRAGMA table_info(orders)").fetchall()
    }

    assert set(columns) == set(EXPECTED_COLUMNS), (
        f"orders table columns {set(columns)} don't match expected {set(EXPECTED_COLUMNS)}"
    )
    for name, (expected_type, expected_notnull) in EXPECTED_COLUMNS.items():
        actual_type, actual_notnull = columns[name]
        assert actual_type == expected_type, f"{name}: expected type {expected_type}, got {actual_type}"
        assert actual_notnull == expected_notnull, (
            f"{name}: expected NOT NULL={bool(expected_notnull)}, got {bool(actual_notnull)}"
        )


def test_orders_has_autoincrement_primary_key(conn):
    columns = conn.execute("PRAGMA table_info(orders)").fetchall()
    pk_columns = [row[1] for row in columns if row[5] == 1]
    assert pk_columns == ["id"], f"expected 'id' as sole primary key, got {pk_columns}"


def test_expected_indexes_exist(conn):
    indexes = {
        row[1] for row in conn.execute("PRAGMA index_list(orders)").fetchall()
    }
    assert "idx_orders_order_date" in indexes
    assert "idx_orders_file_number" in indexes


def test_same_file_number_can_have_multiple_rows(conn):
    # The raw catalogue has multiple documents (Order, ExParte Order, Review
    # Order) sharing one file_number, so the schema must allow that.
    row = (
        "LTB-C-001226-26",
        "2026-04-01",
        "C4",
        "Order",
        "HAMILTON",
        "https://example.com/doc1.pdf",
    )
    conn.execute(
        "INSERT INTO orders (file_number, order_date, issue_codes, document_type, city, view_order_url) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        row,
    )
    conn.execute(
        "INSERT INTO orders (file_number, order_date, issue_codes, document_type, city, view_order_url) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (row[0], "2026-01-08", "C4", "ExParte Order", row[4], "https://example.com/doc2.pdf"),
    )

    count = conn.execute(
        "SELECT COUNT(*) FROM orders WHERE file_number = ?", (row[0],)
    ).fetchone()[0]
    assert count == 2


def test_city_is_nullable_but_other_required_fields_are_not(conn):
    conn.execute(
        "INSERT INTO orders (file_number, order_date, issue_codes, document_type, city, view_order_url) "
        "VALUES ('LTB-1', '2026-01-01', 'T1', 'Order', NULL, 'https://example.com/doc.pdf')"
    )

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO orders (file_number, order_date, issue_codes, document_type, city, view_order_url) "
            "VALUES (NULL, '2026-01-01', 'T1', 'Order', 'LONDON', 'https://example.com/doc.pdf')"
        )
