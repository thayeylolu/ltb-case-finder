"""Task 8/11: translates between user-facing issue names and LTB
application codes, using the mapping from config/issue_taxonomy.json
(Task 3).
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_PATH = PROJECT_ROOT / "config" / "issue_taxonomy.json"


def _load_taxonomy_maps() -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Builds both directions of Task 3's code<->categories mapping:
    issue name -> codes (e.g. "Maintenance" -> ["L6", "T6"]) and
    code -> issue names (e.g. "L1" -> ["Rent and Payment", "Tenancy Eviction"]).
    """
    with TAXONOMY_PATH.open(encoding="utf-8") as f:
        taxonomy = json.load(f)

    issue_to_codes: Dict[str, List[str]] = {}
    code_to_issues: Dict[str, List[str]] = {}
    for form in taxonomy["forms"]:
        code_to_issues[form["code"]] = form["categories"]
        for category in form["categories"]:
            issue_to_codes.setdefault(category, []).append(form["code"])
    return issue_to_codes, code_to_issues


# Loaded once at import time — config/issue_taxonomy.json only changes when
# the taxonomy itself is edited, not per-request.
ISSUE_TO_CODES, CODE_TO_ISSUES = _load_taxonomy_maps()


def get_codes_for_issues(issue_names: List[str]) -> List[str]:
    """Returns the LTB application codes for one or more user-facing issue
    names (plan.md section 3.2), de-duplicated and in first-seen order.

    Raises ValueError if any issue name isn't one of the known MVP 0
    categories.
    """
    codes: List[str] = []
    for issue_name in issue_names:
        if issue_name not in ISSUE_TO_CODES:
            raise ValueError(f"Unknown issue name: {issue_name!r}")
        for code in ISSUE_TO_CODES[issue_name]:
            if code not in codes:
                codes.append(code)
    return codes


def get_issue_names_for_codes(codes: List[str]) -> List[str]:
    """Reverse of get_codes_for_issues: maps an order's own LTB application
    codes back to human-readable issue names for display (plan.md section
    3.2, Step 3), de-duplicated and in first-seen order. Unknown codes are
    skipped rather than raised on, since they come from catalogue data, not
    user input.
    """
    names: List[str] = []
    for code in codes:
        for name in CODE_TO_ISSUES.get(code, []):
            if name not in names:
                names.append(name)
    return names
