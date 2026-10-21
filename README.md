# SQL Query Playground

[![CI](https://github.com/Reaver1000/sql-query-builder/actions/workflows/ci.yml/badge.svg)](https://github.com/Reaver1000/sql-query-builder/actions/workflows/ci.yml)

**Live demo (Hugging Face — DuckDB compiled to WebAssembly, the whole engine runs in your browser):** [reaver1000-sql-query-playground.static.hf.space](https://reaver1000-sql-query-playground.static.hf.space)

**Also live on Streamlit Cloud:** [sql-query-builder-uzsrs2gl2af8avqsxappchw.streamlit.app](https://sql-query-builder-uzsrs2gl2af8avqsxappchw.streamlit.app)

An interactive SQL playground built with Streamlit and DuckDB. It contains **55 tested query templates**, and the test suite executes every template against a deterministic sample database so the claim cannot silently drift.

```bash
pip install -r requirements.txt
streamlit run app.py    # the playground
pytest                  # 115 tests: every template must run and return rows
```

## What it is

- A seeded, deterministic in-memory e-commerce database (4 tables: `customers`, `products`, `orders`, `order_items`; ~19k rows) — same data on every run.
- A query editor with timing, auto-charting (bar/line/pie/scatter/area), and CSV/JSON export.
- A template library organised by what it teaches:

| Category | Templates | Highlights |
|---|---|---|
| Basics | 6 | computed columns, `USING SAMPLE`, per-table row counts |
| Filtering | 6 | anti-joins with `NOT EXISTS`, `CASE` bucketing |
| Joins | 7 | four-table joins, self joins, date spines with `generate_series`, filter-in-`ON` semantics |
| Aggregation | 7 | `FILTER` pivots, `ROLLUP` subtotals, percentiles, `STRING_AGG` |
| Date & Time | 6 | `DATE_TRUNC`, weekday/hour patterns, signup-to-first-order gaps |
| Window Functions | 8 | `QUALIFY`, running totals, moving averages, `LAG` growth, `NTILE` |
| CTEs & Subqueries | 6 | multi-CTE funnels, correlated subqueries, recursive month spine |
| Business Analytics | 9 | Pareto 80/20, RFM scoring, cohort retention, market basket, new-vs-returning revenue |

## Why the templates are tested

The original version of this repo claimed "50+ templates" and shipped 8. The fix was structural, not just writing more: `tests/test_templates.py` parametrises over the whole library and fails if any template errors, returns zero rows, or if the count drops below 50. The claim is now enforced by CI.

## Design notes

- **DuckDB over SQLite** for the analytical dialect: `QUALIFY`, `FILTER`, `ROLLUP`, `PERCENTILE_CONT`, and date `generate_series` all appear in the library.
- **Deterministic sample data** (seeded RNG in `sample_data.py`) so template output is reproducible and testable.
- **Templates live in data, not UI code** (`templates.py` / `templates_advanced.py`) — the app renders whatever the library contains, and the tests import the same source of truth.
