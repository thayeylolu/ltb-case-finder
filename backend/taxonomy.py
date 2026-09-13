"""Task 8: translates user-facing issue names into LTB application codes,
using the mapping from config/issue_taxonomy.json (Task 3).
"""

import json
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_PATH = PROJECT_ROOT / "config" / "issue_taxonomy.json"


def _load_issue_to_codes() -> Dict[str, List[str]]:
    """Inverts Task 3's code->categories mapping into issue name->codes,
    e.g. "Maintenance" -> ["L6", "T6"]."""
    with TAXONOMY_PATH.open(encoding="utf-8") as f:
        taxonomy = json.load(f)

    issue_to_codes: Dict[str, List[str]] = {}
    for form in taxonomy["forms"]:
        for category in form["categories"]:
            issue_to_codes.setdefault(category, []).append(form["code"])
    return issue_to_codes


# Loaded once at import time — config/issue_taxonomy.json only changes when
# the taxonomy itself is edited, not per-request.
ISSUE_TO_CODES = _load_issue_to_codes()


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
