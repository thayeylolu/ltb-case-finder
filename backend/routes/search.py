"""Task 11: POST /search — wires the issue lookup (Task 8), case filtering
(Task 9), and ranking (Task 10) into one JSON API, per architecture.md's
request lifecycle.
"""

import sqlite3
from typing import Generator

from fastapi import APIRouter, Depends, HTTPException

from backend.queries import find_orders_matching_all_codes, find_orders_matching_any_code, get_connection
from backend.ranking import rank_and_limit_results
from backend.schemas import CaseResult, SearchRequest, SearchResponse
from backend.taxonomy import get_codes_for_issues, get_issue_names_for_codes

router = APIRouter()


def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    connection = get_connection()
    try:
        yield connection
    finally:
        connection.close()


@router.post("/search", response_model=SearchResponse)
def search(
    request: SearchRequest,
    connection: sqlite3.Connection = Depends(get_db_connection),
) -> SearchResponse:
    try:
        codes = get_codes_for_issues(request.issues)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    all_match_results = find_orders_matching_all_codes(connection, codes)
    any_match_results = find_orders_matching_any_code(connection, codes)
    ranked_results = rank_and_limit_results(all_match_results, any_match_results)

    results = []
    for record in ranked_results:
        codes = [code.strip() for code in record["issue_codes"].split(";") if code.strip()]
        results.append(
            CaseResult(
                file_number=record["file_number"],
                order_date=record["order_date"],
                issues=get_issue_names_for_codes(codes),
                forms=codes,
                city=record["city"].title() if record["city"] else None,
                resident_type=record["resident_type"],
                address=record["address"],
                document_type=record["document_type"],
                view_order_url=record["view_order_url"],
            )
        )

    return SearchResponse(results=results)
