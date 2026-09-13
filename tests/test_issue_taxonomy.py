"""Task 3: verifies the issue taxonomy mapping (config/issue_taxonomy.json)."""

import json
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_PATH = PROJECT_ROOT / "config" / "issue_taxonomy.json"
README_PATH = PROJECT_ROOT / "config" / "README.md"

# The 14 MVP 0 issue categories (docs/mvp0/plan.md section 3.2).
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

CODE_PATTERN = re.compile(r"^[A-Z]\d+$")


@pytest.fixture(scope="module")
def taxonomy():
    with TAXONOMY_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def test_taxonomy_file_is_valid_json_with_forms_list(taxonomy):
    assert "forms" in taxonomy
    assert isinstance(taxonomy["forms"], list)
    assert len(taxonomy["forms"]) > 0


def test_every_form_has_required_fields(taxonomy):
    for form in taxonomy["forms"]:
        assert "code" in form and isinstance(form["code"], str) and form["code"]
        assert "name" in form and isinstance(form["name"], str) and form["name"]
        assert "categories" in form and isinstance(form["categories"], list) and form["categories"]


def test_codes_match_expected_pattern_and_are_unique(taxonomy):
    codes = [form["code"] for form in taxonomy["forms"]]

    for code in codes:
        assert CODE_PATTERN.match(code), f"code '{code}' doesn't match the expected LETTER+DIGITS pattern"

    assert len(codes) == len(set(codes)), "duplicate codes found in issue_taxonomy.json"


def test_all_expected_categories_are_covered(taxonomy):
    categories_in_use = set()
    for form in taxonomy["forms"]:
        categories_in_use.update(form["categories"])

    missing = EXPECTED_CATEGORIES - categories_in_use
    assert not missing, f"categories from plan.md with no mapped codes: {missing}"

    unexpected = categories_in_use - EXPECTED_CATEGORIES
    assert not unexpected, f"categories in taxonomy not defined in plan.md: {unexpected}"


def test_arrears_and_breached_conditions_map_to_expected_codes(taxonomy):
    by_code = {form["code"]: form["categories"] for form in taxonomy["forms"]}

    assert by_code["C1"].count("Arrears") == 1, "expected only C1 to be tagged Arrears"
    for code, categories in by_code.items():
        if code != "C1":
            assert "Arrears" not in categories, f"did not expect {code} to be tagged Arrears"

    for code in ("L4", "T4", "T5", "C4"):
        assert "Breached Conditions" in by_code[code], f"expected {code} to be tagged Breached Conditions"


def test_coop_codes_are_tagged_coop_housing(taxonomy):
    by_code = {form["code"]: form["categories"] for form in taxonomy["forms"]}

    for code in ("C1", "C2", "C3", "C4"):
        assert code in by_code, f"expected co-op code {code} to be present"
        assert "Co-op Housing" in by_code[code], f"expected {code} to be tagged Co-op Housing"


def test_readme_documents_both_sources():
    content = README_PATH.read_text(encoding="utf-8")
    assert "tribunalsontario.ca/ltb/forms-filing-and-fees" in content
    assert "tribunalsontario.ca/ltb/non-profit-co-op-evictions" in content
