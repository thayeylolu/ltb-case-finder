"""Task 15: verifies the no-results messaging and legal disclaimer
(frontend/app.js, frontend/index.html).

No JS runtime is set up in this project (Python + pytest only, per
CLAUDE.md's "Local dev environment"), so — consistent with Tasks 12-14 —
this inspects the page/script source for the required behavior rather than
executing it. The actual rendering was verified manually in Chrome.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_JS_PATH = PROJECT_ROOT / "frontend" / "app.js"
INDEX_HTML_PATH = PROJECT_ROOT / "frontend" / "index.html"


def _read_app_js() -> str:
    return APP_JS_PATH.read_text(encoding="utf-8")


def _read_index_html() -> str:
    return INDEX_HTML_PATH.read_text(encoding="utf-8")


def test_no_results_message_is_shown_when_results_are_empty():
    content = _read_app_js()
    assert "results.length === 0" in content
    assert "No matching orders found" in content


def test_no_results_message_is_appended_to_the_results_container():
    content = _read_app_js()
    match = re.search(
        r"results\.length === 0\)\s*\{([^}]*)\}",
        content,
        re.DOTALL,
    )
    assert match, "expected an if-block handling the zero-results case"
    branch = match.group(1)
    assert "container.appendChild" in branch


def test_disclaimer_is_present_and_visible_in_the_html():
    content = _read_index_html()
    assert 'id="disclaimer"' in content
    assert "not provide legal advice" in content
    assert "outcome" in content.lower()


def test_disclaimer_is_persistent_rather_than_only_shown_with_results():
    # The disclaimer must be static markup in the page (always visible),
    # not something app.js only injects alongside search results.
    html_content = _read_index_html()
    disclaimer_match = re.search(
        r'<header>.*?<p id="disclaimer".*?</p>.*?</header>',
        html_content,
        re.DOTALL,
    )
    assert disclaimer_match, "disclaimer should live in the persistent page header"

    js_content = _read_app_js()
    assert "disclaimer" not in js_content
