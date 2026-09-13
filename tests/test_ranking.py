"""Task 10: verifies ranking + capping logic (backend/ranking.py)."""

from backend.ranking import rank_and_limit_results


def _record(record_id, order_date):
    return {"id": record_id, "order_date": order_date, "file_number": f"LTB-{record_id}"}


def test_all_match_results_are_sorted_by_most_recent_date():
    all_matches = [_record(1, "2026-01-01"), _record(2, "2026-03-01"), _record(3, "2026-02-01")]
    result = rank_and_limit_results(all_matches, any_match_results=all_matches)
    assert [r["id"] for r in result] == [2, 3, 1]


def test_all_matches_always_rank_ahead_of_any_only_matches_regardless_of_date():
    all_matches = [_record(10, "2020-01-01")]
    any_matches = [_record(10, "2020-01-01"), _record(20, "2030-01-01")]

    result = rank_and_limit_results(all_matches, any_matches)

    assert [r["id"] for r in result] == [10, 20], (
        "an ALL-match case must rank first even when an ANY-only case has a more recent date"
    )


def test_any_match_duplicates_of_all_matches_are_not_repeated():
    all_matches = [_record(1, "2026-01-01"), _record(2, "2026-02-01")]
    any_matches = [_record(1, "2026-01-01"), _record(2, "2026-02-01"), _record(3, "2026-03-01")]

    result = rank_and_limit_results(all_matches, any_matches)

    assert [r["id"] for r in result] == [2, 1, 3]
    assert len(result) == 3


def test_fewer_than_limit_full_matches_falls_back_to_any_match_results():
    # 3 ALL-matches; ANY-matches include those same 3 plus 25 more distinct
    # cases — more than enough to exceed the 20-result cap once combined.
    all_matches = [_record(1, "2026-01-01"), _record(2, "2026-01-03"), _record(3, "2026-01-02")]
    extra_any_only = [_record(100 + day, f"2026-02-{day:02d}") for day in range(4, 29)]  # 25 records
    any_matches = all_matches + extra_any_only

    result = rank_and_limit_results(all_matches, any_matches)

    assert len(result) == 20
    # ALL-matches first, sorted most-recent-first.
    assert [r["id"] for r in result[:3]] == [2, 3, 1]
    # Remaining 17 slots filled by the most recent ANY-only cases (days 28
    # down to 12), most-recent-first.
    expected_fallback_ids = [100 + day for day in range(28, 11, -1)]
    assert [r["id"] for r in result[3:]] == expected_fallback_ids


def test_combined_results_under_the_limit_are_all_returned():
    all_matches = [_record(1, "2026-01-01")]
    any_matches = [_record(1, "2026-01-01"), _record(2, "2026-01-02")]

    result = rank_and_limit_results(all_matches, any_matches)

    assert len(result) == 2


def test_no_matches_returns_empty_list():
    assert rank_and_limit_results([], []) == []
