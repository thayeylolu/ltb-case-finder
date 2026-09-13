"""Task 13: verifies the Search-button-to-API wiring (frontend/app.js).

No JS runtime is set up in this project (Python + pytest only, per
CLAUDE.md's "Local dev environment"), so — consistent with how Task 12's
static HTML was checked — this inspects the script's source for the
integration points the task requires rather than executing it. The actual
end-to-end behavior was verified manually in Chrome.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_JS_PATH = PROJECT_ROOT / "frontend" / "app.js"
INDEX_HTML_PATH = PROJECT_ROOT / "frontend" / "index.html"


def _read_app_js() -> str:
    return APP_JS_PATH.read_text(encoding="utf-8")


def test_app_js_exists_and_is_non_empty():
    assert APP_JS_PATH.exists(), "frontend/app.js is missing"
    assert APP_JS_PATH.stat().st_size > 0, "frontend/app.js is empty"


def test_app_js_is_linked_from_index_html():
    content = INDEX_HTML_PATH.read_text(encoding="utf-8")
    assert 'src="app.js"' in content


def test_search_button_click_is_wired_up():
    content = _read_app_js()
    assert re.search(r"""getElementById\(["']search-button["']\)""", content)
    assert re.search(r"""addEventListener\(["']click["']""", content)


def test_selected_issue_checkboxes_are_collected():
    content = _read_app_js()
    assert re.search(r"""name=\\?["']issues\\?["']""", content)
    assert ":checked" in content


def test_posts_to_search_endpoint_as_json():
    content = _read_app_js()
    assert "/search" in content
    assert re.search(r"""method\s*:\s*["']POST["']""", content)
    assert "application/json" in content


def test_handles_no_issues_selected_without_a_network_call():
    content = _read_app_js()
    assert "issues.length === 0" in content or "!issues.length" in content


def test_handles_non_ok_http_responses():
    content = _read_app_js()
    assert "response.ok" in content


def test_handles_fetch_rejection():
    content = _read_app_js()
    assert re.search(r"\bcatch\b", content)
