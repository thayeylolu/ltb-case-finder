"""Task 11: integration test for POST /search — wires taxonomy (Task 8),
filtering (Task 9), and ranking (Task 10) behind the FastAPI route.
"""

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.routes.search import get_db_connection

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "data" / "schema.sql"

# LTB-D matches every code for "Tenant Rights" + "Maintenance" (T2, L6, T6);
# LTB-A and LTB-B match only some of them; LTB-C is unrelated (L5).
SEED_ORDERS = [
    # file_number, order_date, issue_codes, document_type, city, resident_type, address, view_order_url, codes
    (
        "LTB-D",
        "2026-08-01",
        "T2;T6;L6",
        "Order",
        "TORONTO",
        "Rental Unit",
        "1 KING ST, TORONTO, ON M5H1A1",
        "https://example.com/d.pdf",
        ["T2", "T6", "L6"],
    ),
    ("LTB-B", "2026-06-01", "T2", "Order", "TORONTO", "Complex", "50 BAY ST, TORONTO, ON M5J2N8", "https://example.com/b.pdf", ["T2"]),
    ("LTB-A", "2026-05-01", "T2;T6", "Order", "LONDON", "", "", "https://example.com/a.pdf", ["T2", "T6"]),
    ("LTB-C", "2026-01-01", "L5", "Order", "OTTAWA", "", "", "https://example.com/c.pdf", ["L5"]),
]


@pytest.fixture()
def seeded_db_path(tmp_path):
    db_path = tmp_path / "test_ltb.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    for file_number, order_date, issue_codes, document_type, city, resident_type, address, view_order_url, codes in SEED_ORDERS:
        cursor = conn.execute(
            "INSERT INTO orders "
            "(file_number, order_date, issue_codes, document_type, city, resident_type, address, view_order_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (file_number, order_date, issue_codes, document_type, city, resident_type, address, view_order_url),
        )
        order_id = cursor.lastrowid
        conn.executemany(
            "INSERT INTO order_issue_codes (order_id, code) VALUES (?, ?)",
            [(order_id, code) for code in codes],
        )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture()
def client(seeded_db_path):
    def override_get_db_connection():
        connection = sqlite3.connect(seeded_db_path)
        try:
            yield connection
        finally:
            connection.close()

    app.dependency_overrides[get_db_connection] = override_get_db_connection
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_search_ranks_all_match_ahead_and_excludes_unrelated_orders(client):
    response = client.post("/search", json={"issues": ["Tenant Rights", "Maintenance"]})

    assert response.status_code == 200
    body = response.json()
    file_numbers = [r["file_number"] for r in body["results"]]

    # LTB-D matches all 3 codes (T2, T6, L6); LTB-B and LTB-A match only
    # some, ranked after by most recent date; LTB-C (L5) never appears.
    assert file_numbers == ["LTB-D", "LTB-B", "LTB-A"]


def test_search_maps_codes_to_human_readable_issue_names(client):
    response = client.post("/search", json={"issues": ["Tenant Rights", "Maintenance"]})

    result_d = next(r for r in response.json()["results"] if r["file_number"] == "LTB-D")
    assert set(result_d["issues"]) == {"Tenant Rights", "Maintenance"}


def test_search_result_has_expected_fields(client):
    response = client.post("/search", json={"issues": ["Tenant Rights"]})

    result = response.json()["results"][0]
    assert set(result.keys()) == {
        "file_number",
        "order_date",
        "issues",
        "forms",
        "city",
        "resident_type",
        "address",
        "document_type",
        "view_order_url",
    }


def test_search_with_unknown_issue_returns_400(client):
    response = client.post("/search", json={"issues": ["Not A Real Issue"]})
    assert response.status_code == 400


def test_search_requires_at_least_one_issue(client):
    response = client.post("/search", json={"issues": []})
    assert response.status_code == 422


def test_search_with_no_matching_cases_returns_empty_results(client):
    response = client.post("/search", json={"issues": ["Care Home Tenancies"]})
    assert response.status_code == 200
    assert response.json()["results"] == []


def test_search_normalizes_city_to_title_case(client):
    # The raw catalogue's city casing is inconsistent (e.g. all-caps); the
    # API should always return it in Title Case.
    response = client.post("/search", json={"issues": ["Tenant Rights"]})

    cities = {r["city"] for r in response.json()["results"]}
    assert cities == {"Toronto", "London"}


def test_search_returns_the_raw_application_codes_as_forms(client):
    response = client.post("/search", json={"issues": ["Tenant Rights", "Maintenance"]})

    result_d = next(r for r in response.json()["results"] if r["file_number"] == "LTB-D")
    assert result_d["forms"] == ["T2", "T6", "L6"]


def test_search_returns_resident_type_and_address_from_the_db(client):
    response = client.post("/search", json={"issues": ["Tenant Rights", "Maintenance"]})
    results = {r["file_number"]: r for r in response.json()["results"]}

    assert results["LTB-D"]["resident_type"] == "Rental Unit"
    assert results["LTB-D"]["address"] == "1 KING ST, TORONTO, ON M5H1A1"
    assert results["LTB-B"]["resident_type"] == "Complex"
    assert results["LTB-B"]["address"] == "50 BAY ST, TORONTO, ON M5J2N8"


def test_search_returns_empty_resident_type_and_address_when_neither_was_in_the_catalogue(client):
    response = client.post("/search", json={"issues": ["Tenant Rights", "Maintenance"]})
    result_a = next(r for r in response.json()["results"] if r["file_number"] == "LTB-A")

    assert result_a["resident_type"] == ""
    assert result_a["address"] == ""
