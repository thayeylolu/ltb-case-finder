"""Task 14: verifies the results table rendering (frontend/app.js).

No JS runtime is set up in this project (Python + pytest only, per
CLAUDE.md's "Local dev environment"), so — consistent with Tasks 12/13 —
this inspects the script's source rather than executing it. The actual
rendering was verified manually in Chrome.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_JS_PATH = PROJECT_ROOT / "frontend" / "app.js"

EXPECTED_COLUMNS = ["File Number", "Order Date", "Issues", "City", "Document Type", "View Order"]


def _read_app_js() -> str:
    return APP_JS_PATH.read_text(encoding="utf-8")


def test_renders_into_the_results_container():
    content = _read_app_js()
    assert re.search(r"""getElementById\(["']results["']\)""", content)


def test_table_has_every_required_column_header():
    content = _read_app_js()
    for column in EXPECTED_COLUMNS:
        assert f'"{column}"' in content, f"missing column header: {column}"


def test_issues_are_joined_with_the_planned_separator():
    content = _read_app_js()
    assert 'join(" · ")' in content or "join(' · ')" in content


def test_view_order_is_a_link_opening_in_a_new_tab():
    content = _read_app_js()
    assert "view_order_url" in content
    assert '_blank' in content
    assert "noopener" in content


def test_search_click_handler_renders_results():
    content = _read_app_js()
    assert "renderResults(" in content
