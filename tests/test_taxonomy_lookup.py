"""Task 8: verifies the issue name -> LTB code lookup service (backend/taxonomy.py)."""

import pytest

from backend.taxonomy import get_codes_for_issues


def test_single_issue_returns_its_codes():
    assert get_codes_for_issues(["Tenant Rights"]) == ["T2"]


def test_single_issue_with_multiple_codes():
    assert sorted(get_codes_for_issues(["Maintenance"])) == ["L6", "T6"]


def test_multiple_issues_returns_union_of_codes_deduped():
    codes = get_codes_for_issues(["Maintenance", "Tenant Rights"])
    assert sorted(codes) == ["L6", "T2", "T6"]

    # "Tenancy Eviction" and "Rent and Payment" both include L1 and L2 —
    # the shared codes should appear only once in the combined result.
    combined = get_codes_for_issues(["Tenancy Eviction", "Rent and Payment"])
    assert sorted(set(combined)) == sorted(combined)
    assert "L1" in combined and "L2" in combined


def test_unknown_issue_name_raises_value_error():
    with pytest.raises(ValueError):
        get_codes_for_issues(["Not A Real Issue"])


def test_unknown_issue_name_among_valid_ones_still_raises():
    with pytest.raises(ValueError):
        get_codes_for_issues(["Maintenance", "Not A Real Issue"])
