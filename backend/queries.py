"""Task 9: DB access — filters orders by LTB application code, per the two
query modes in plan.md section 4 (ALL selected codes / ANY selected code).

Queries against order_issue_codes (Task 6) rather than orders.issue_codes
directly, so filtering is an indexed exact match instead of a LIKE '%T1%'
scan that would also wrongly match "T10", "T11", ...
"""

import sqlite3
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "ltb.db"

ORDER_COLUMNS = ("id", "file_number", "order_date", "issue_codes", "document_type", "city", "view_order_url")

ORDER_SELECT_COLUMNS = "o.id, o.file_number, o.order_date, o.issue_codes, o.document_type, o.city, o.view_order_url"


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


def _rows_to_dicts(rows) -> List[Dict]:
    return [dict(zip(ORDER_COLUMNS, row)) for row in rows]


def find_orders_matching_all_codes(connection: sqlite3.Connection, codes: List[str]) -> List[Dict]:
    """Orders whose codes include every one of `codes` — the strongest
    matches (plan.md section 4). Most recent order_date first."""
    if not codes:
        return []

    placeholders = ",".join("?" for _ in codes)
    sql = f"""
        SELECT {ORDER_SELECT_COLUMNS}
        FROM orders o
        JOIN order_issue_codes oic ON oic.order_id = o.id
        WHERE oic.code IN ({placeholders})
        GROUP BY o.id
        HAVING COUNT(DISTINCT oic.code) = ?
        ORDER BY o.order_date DESC
    """
    cursor = connection.execute(sql, (*codes, len(codes)))
    return _rows_to_dicts(cursor.fetchall())


def find_orders_matching_any_code(connection: sqlite3.Connection, codes: List[str]) -> List[Dict]:
    """Orders whose codes include at least one of `codes` — the fallback
    match set (plan.md section 4). Most recent order_date first."""
    if not codes:
        return []

    placeholders = ",".join("?" for _ in codes)
    sql = f"""
        SELECT DISTINCT {ORDER_SELECT_COLUMNS}
        FROM orders o
        JOIN order_issue_codes oic ON oic.order_id = o.id
        WHERE oic.code IN ({placeholders})
        ORDER BY o.order_date DESC
    """
    cursor = connection.execute(sql, codes)
    return _rows_to_dicts(cursor.fetchall())
