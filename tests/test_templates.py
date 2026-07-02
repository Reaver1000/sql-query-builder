"""Every template in the library must execute against the sample database.

This is the test that keeps the README's "50+ tested templates" claim true:
a template that errors, returns nothing, or gets dropped breaks the build.
"""

import duckdb
import pytest

from sample_data import TABLES, create_database
from templates import TEMPLATES, all_templates, template_count

ALL = list(all_templates())


@pytest.fixture(scope="module")
def conn():
    return create_database()


def test_library_has_at_least_50_templates():
    assert template_count() >= 50


def test_every_category_is_nonempty():
    for category, templates in TEMPLATES.items():
        assert templates, f"Category {category!r} is empty"


def test_template_names_are_unique():
    names = [t["name"] for _, t in ALL]
    assert len(names) == len(set(names))


def test_sample_database_tables_exist(conn):
    existing = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    assert set(TABLES) <= existing


def test_sample_database_is_deterministic():
    a = create_database().execute("SELECT SUM(total_amount) FROM orders").fetchone()[0]
    b = create_database().execute("SELECT SUM(total_amount) FROM orders").fetchone()[0]
    assert a == b


@pytest.mark.parametrize(
    "category,template",
    ALL,
    ids=[f"{c} :: {t['name']}" for c, t in ALL],
)
def test_template_executes_and_returns_rows(conn, category, template):
    """Each template runs without error and returns at least one row."""
    try:
        df = conn.execute(template["query"]).df()
    except duckdb.Error as e:  # pragma: no cover - failure message aid
        pytest.fail(f"{category} :: {template['name']} failed: {e}")
    assert len(df) > 0, f"{category} :: {template['name']} returned no rows"
    assert len(df.columns) > 0


@pytest.mark.parametrize(
    "category,template",
    ALL,
    ids=[f"{c} :: {t['name']}" for c, t in ALL],
)
def test_template_has_name_and_description(category, template):
    assert template["name"].strip()
    assert template["description"].strip()
    assert "SELECT" in template["query"].upper()
