"""Task 9: verifies the ALL-match / ANY-match case filtering queries (backend/queries.py)."""

import sqlite3
from pathlib import Path

import pytest

from backend.queries import find_orders_matching_all_codes, find_orders_matching_any_code

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "data" / "schema.sql"

# Seed data, deliberately covering: an order matching all of T1+T2, one
# matching only T1, one matching only T2, one unrelated (T3 only), and one
# matching all of T1+T2 plus an extra code, to prove ALL-match isn't an
# exact-set match.
SEED_ORDERS = [
    # file_number, order_date, issue_codes, document_type, city, view_order_url, codes
    ("LTB-A", "2026-05-01", "T1;T2", "Order", "LONDON", "https://example.com/a.pdf", ["T1", "T2"]),
    ("LTB-B", "2026-04-01", "T1", "Order", "LONDON", "https://example.com/b.pdf", ["T1"]),
    ("LTB-C", "2026-06-01", "T2", "Order", "LONDON", "https://example.com/c.pdf", ["T2"]),
    ("LTB-D", "2026-01-01", "T3", "Order", "LONDON", "https://example.com/d.pdf", ["T3"]),
    ("LTB-E", "2026-07-01", "T1;T2;T3", "Order", "LONDON", "https://example.com/e.pdf", ["T1", "T2", "T3"]),
]


@pytest.fixture()
def seeded_conn():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    for file_number, order_date, issue_codes, document_type, city, view_order_url, codes in SEED_ORDERS:
        cursor = conn.execute(
            "INSERT INTO orders (file_number, order_date, issue_codes, document_type, city, view_order_url) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (file_number, order_date, issue_codes, document_type, city, view_order_url),
        )
        order_id = cursor.lastrowid
        conn.executemany(
            "INSERT INTO order_issue_codes (order_id, code) VALUES (?, ?)",
            [(order_id, code) for code in codes],
        )
    conn.commit()

    yield conn
    conn.close()


def test_all_codes_match_requires_every_selected_code(seeded_conn):
    results = find_orders_matching_all_codes(seeded_conn, ["T1", "T2"])
    file_numbers = [row["file_number"] for row in results]
    assert file_numbers == ["LTB-E", "LTB-A"], "expected only orders containing BOTH T1 and T2, most recent first"


def test_all_codes_match_with_a_single_code(seeded_conn):
    results = find_orders_matching_all_codes(seeded_conn, ["T2"])
    file_numbers = {row["file_number"] for row in results}
    assert file_numbers == {"LTB-A", "LTB-C", "LTB-E"}


def test_any_code_match_requires_at_least_one_selected_code(seeded_conn):
    results = find_orders_matching_any_code(seeded_conn, ["T1", "T2"])
    file_numbers = [row["file_number"] for row in results]
    assert file_numbers == ["LTB-E", "LTB-C", "LTB-A", "LTB-B"], (
        "expected every order containing T1 OR T2 (not T3-only LTB-D), most recent first"
    )


def test_any_code_match_does_not_duplicate_a_row_matching_multiple_codes(seeded_conn):
    results = find_orders_matching_any_code(seeded_conn, ["T1", "T2"])
    file_numbers = [row["file_number"] for row in results]
    assert file_numbers.count("LTB-E") == 1, "LTB-E matches both T1 and T2 but should appear once"


def test_no_matches_returns_empty_list(seeded_conn):
    assert find_orders_matching_all_codes(seeded_conn, ["Z9"]) == []
    assert find_orders_matching_any_code(seeded_conn, ["Z9"]) == []


def test_empty_code_list_returns_empty_list(seeded_conn):
    assert find_orders_matching_all_codes(seeded_conn, []) == []
    assert find_orders_matching_any_code(seeded_conn, []) == []


def test_result_records_include_expected_fields(seeded_conn):
    results = find_orders_matching_all_codes(seeded_conn, ["T1", "T2", "T3"])
    assert results == [
        {
            "id": results[0]["id"],
            "file_number": "LTB-E",
            "order_date": "2026-07-01",
            "issue_codes": "T1;T2;T3",
            "document_type": "Order",
            "city": "LONDON",
            "resident_type": "",
            "view_order_url": "https://example.com/e.pdf",
        }
    ]
