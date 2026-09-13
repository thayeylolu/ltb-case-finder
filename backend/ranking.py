"""Task 10: combines ALL-match and ANY-match query results (Task 9) into a
single ranked, capped list, per plan.md section 4.
"""

from typing import Dict, List

MAX_RESULTS = 20


def _sorted_by_recent_date(records: List[Dict]) -> List[Dict]:
    return sorted(records, key=lambda record: record["order_date"], reverse=True)


def rank_and_limit_results(
    all_match_results: List[Dict],
    any_match_results: List[Dict],
    limit: int = MAX_RESULTS,
) -> List[Dict]:
    """Ranks cases matching every selected issue ahead of cases matching at
    least one, each sorted by most recent order date, capped at `limit`.

    `any_match_results` is expected to be a superset of `all_match_results`
    (Task 9's ANY-match query naturally returns every ALL-match row too, plus
    more) — those overlapping rows are excluded from the fallback so no case
    appears twice in the combined list.
    """
    ranked_all_matches = _sorted_by_recent_date(all_match_results)
    matched_ids = {record["id"] for record in ranked_all_matches}

    fallback_matches = [record for record in any_match_results if record["id"] not in matched_ids]
    ranked_fallback_matches = _sorted_by_recent_date(fallback_matches)

    combined = ranked_all_matches + ranked_fallback_matches
    return combined[:limit]
