"""Task 12: verifies the static issue-selection page (frontend/index.html)."""

from html.parser import HTMLParser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML_PATH = PROJECT_ROOT / "frontend" / "index.html"
STYLES_CSS_PATH = PROJECT_ROOT / "frontend" / "styles.css"

# The 14 MVP 0 issue categories (docs/mvp0/plan.md section 3.2), matching
# tests/test_issue_taxonomy.py's EXPECTED_CATEGORIES.
EXPECTED_CATEGORIES = {
    "Rent and Payment",
    "Tenancy Eviction",
    "Tenancy Ending",
    "Notice",
    "Breached Conditions",
    "Rent Change",
    "Maintenance",
    "Care Home Tenancies",
    "Locks and Access",
    "Tenancy Agreements",
    "Tenant Rights",
    "Suite Meters",
    "Co-op Housing",
    "Arrears",
}


class IssueSelectionPageParser(HTMLParser):
    """Collects checkbox input values and button text from the page."""

    def __init__(self):
        super().__init__()
        self.checkbox_values = []
        self._in_button = False
        self.button_texts = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == "input" and attr_dict.get("type") == "checkbox":
            self.checkbox_values.append(attr_dict.get("value"))
        if tag == "button":
            self._in_button = True

    def handle_endtag(self, tag):
        if tag == "button":
            self._in_button = False

    def handle_data(self, data):
        if self._in_button:
            self.button_texts.append(data.strip())


def _parse_index_html():
    parser = IssueSelectionPageParser()
    parser.feed(INDEX_HTML_PATH.read_text(encoding="utf-8"))
    return parser


def test_index_html_and_styles_css_exist():
    assert INDEX_HTML_PATH.exists(), "frontend/index.html is missing"
    assert STYLES_CSS_PATH.exists(), "frontend/styles.css is missing"
    assert STYLES_CSS_PATH.stat().st_size > 0, "frontend/styles.css is empty"


def test_page_has_a_checkbox_for_every_mvp0_issue_category():
    parser = _parse_index_html()
    assert set(parser.checkbox_values) == EXPECTED_CATEGORIES


def test_page_has_no_duplicate_checkboxes():
    parser = _parse_index_html()
    assert len(parser.checkbox_values) == len(EXPECTED_CATEGORIES)


def test_page_has_a_search_button():
    parser = _parse_index_html()
    assert any("Search" in text for text in parser.button_texts)


def test_stylesheet_is_linked():
    content = INDEX_HTML_PATH.read_text(encoding="utf-8")
    assert 'href="styles.css"' in content


def test_checkboxes_are_listed_in_alphabetical_order():
    parser = _parse_index_html()
    assert parser.checkbox_values == sorted(parser.checkbox_values, key=str.lower)
