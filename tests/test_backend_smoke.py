"""Task 16: end-to-end backend smoke test.

Exercises the real wiring — a seeded SQLite DB, the real FastAPI app
(Tasks 8-11), and a real HTTP request via FastAPI's TestClient — rather
than unit-testing each layer in isolation the way tests/test_search_endpoint.py
and friends do. Confirms the full flow produces the expected case fields
and respects the 20-result cap from plan.md section 4.
"""

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.routes.search import get_db_connection

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "data" / "schema.sql"

EXPECTED_RESULT_FIELDS = {
    "file_number",
    "order_date",
    "issues",
    "forms",
    "city",
    "resident_type",
    "document_type",
    "view_order_url",
}


@pytest.fixture()
def seeded_db_path(tmp_path):
    db_path = tmp_path / "smoke_ltb.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    # 25 "Maintenance" (T6) orders on distinct dates — one more than the
    # 20-result cap, so the smoke test actually exercises it rather than
    # just returning everything.
    for i in range(25):
        cursor = conn.execute(
            "INSERT INTO orders (file_number, order_date, issue_codes, document_type, city, view_order_url) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                f"LTB-SMOKE-{i:03d}",
                f"2026-01-{i + 1:02d}",
                "T6",
                "Order",
                "TORONTO",
                f"https://example.com/smoke-{i}.pdf",
            ),
        )
        order_id = cursor.lastrowid
        conn.execute("INSERT INTO order_issue_codes (order_id, code) VALUES (?, ?)", (order_id, "T6"))

    # An unrelated order that must never show up for a "Maintenance" search.
    cursor = conn.execute(
        "INSERT INTO orders (file_number, order_date, issue_codes, document_type, city, view_order_url) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("LTB-UNRELATED", "2026-02-01", "L5", "Order", "OTTAWA", "https://example.com/unrelated.pdf"),
    )
    order_id = cursor.lastrowid
    conn.execute("INSERT INTO order_issue_codes (order_id, code) VALUES (?, ?)", (order_id, "L5"))

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


def test_search_end_to_end_returns_expected_fields_and_respects_the_cap(client):
    response = client.post("/search", json={"issues": ["Maintenance"]})

    assert response.status_code == 200
    results = response.json()["results"]

    assert len(results) == 20, "expected the plan.md section 4 20-result cap to be enforced"

    for result in results:
        assert set(result.keys()) == EXPECTED_RESULT_FIELDS
        assert "Maintenance" in result["issues"]
        assert result["file_number"] != "LTB-UNRELATED"

    order_dates = [result["order_date"] for result in results]
    assert order_dates == sorted(order_dates, reverse=True), "results should be most-recent-first"
