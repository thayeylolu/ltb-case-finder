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
STYLES_CSS_PATH = PROJECT_ROOT / "frontend" / "styles.css"

EXPECTED_COLUMNS = [
    "File Number",
    "Order Date",
    "Issues",
    "Forms",
    "City",
    "Resident Type",
    "Document Type",
    "View Order",
]


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


def test_forms_column_uses_the_same_separator_as_issues_not_semicolons():
    # User feedback: the "Forms" column should use the "·" notation from
    # Issues instead of the raw catalogue's ";" delimiter.
    content = _read_app_js()
    assert "result.forms" in content
    assert re.search(r"result\.forms\.join\([\"']\s*·\s*[\"']\)", content)


def test_resident_type_must_be_rendered_in_the_results_table():
    content = _read_app_js()
    assert '"Resident Type"' in content
    assert "result.resident_type" in content


def test_address_is_not_rendered_in_the_results_table():
    content = _read_app_js()
    assert '"Address"' not in content
    assert "result.address" not in content


def test_view_order_is_a_link_opening_in_a_new_tab():
    content = _read_app_js()
    assert "view_order_url" in content
    assert '_blank' in content
    assert "noopener" in content


def test_search_click_handler_renders_results():
    content = _read_app_js()
    assert "renderResults(" in content


def test_issues_cell_is_marked_for_text_wrapping():
    # User feedback: a long "·"-joined issues list shouldn't force the row
    # onto one unreadable line.
    js_content = _read_app_js()
    assert 'className = "issues-cell"' in js_content or "className = 'issues-cell'" in js_content

    css_content = STYLES_CSS_PATH.read_text(encoding="utf-8")
    assert re.search(r"\.issues-cell\s*{[^}]*white-space:\s*normal", css_content, re.DOTALL)
