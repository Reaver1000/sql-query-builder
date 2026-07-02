"""SQL Query Playground — Streamlit + DuckDB.

Write and run SQL against a seeded in-memory e-commerce database, or load
any of the 50+ tested templates from the library in ``templates.py``.
"""

from datetime import datetime

import plotly.express as px
import streamlit as st

from sample_data import TABLES, create_database
from templates import TEMPLATES, template_count

st.set_page_config(page_title="SQL Query Playground", page_icon="🔍", layout="wide")


@st.cache_resource
def get_connection():
    return create_database()


def render_sidebar(conn) -> None:
    with st.sidebar:
        st.header("📚 Schema")
        for table in TABLES:
            with st.expander(f"📦 {table}"):
                schema = conn.execute(f"DESCRIBE {table}").df()
                st.dataframe(schema, hide_index=True, use_container_width=True)

        st.markdown("---")
        st.markdown(
            f"**{template_count()} templates** across {len(TEMPLATES)} categories, "
            "from `SELECT ... LIMIT` to cohort retention. Every template is "
            "executed by the test suite (`pytest`)."
        )


def render_query_panel(conn) -> None:
    st.header("📝 SQL Query")

    col_cat, col_tpl = st.columns(2)
    with col_cat:
        category = st.selectbox("Category", ["Custom"] + list(TEMPLATES.keys()))
    template = None
    if category != "Custom":
        with col_tpl:
            names = [t["name"] for t in TEMPLATES[category]]
            chosen = st.selectbox("Template", names)
            template = next(t for t in TEMPLATES[category] if t["name"] == chosen)

    if template:
        st.info(f"**{template['description']}**")
        default_query = template["query"]
    else:
        default_query = "SELECT * FROM orders LIMIT 100"

    query = st.text_area("SQL", value=default_query, height=220)

    if st.button("▶ Run Query", type="primary"):
        try:
            start = datetime.now()
            result = conn.execute(query).df()
            elapsed = (datetime.now() - start).total_seconds()
            st.success(f"✓ {len(result)} rows in {elapsed:.3f}s")
            st.session_state["result"] = result
            st.session_state["query"] = query
        except Exception as e:
            st.error(f"❌ {e}")


def render_stats(conn) -> None:
    st.header("📊 Database")
    stats = {
        "Customers": "SELECT COUNT(*) FROM customers",
        "Orders": "SELECT COUNT(*) FROM orders",
        "Products": "SELECT COUNT(*) FROM products",
        "Completed revenue": "SELECT ROUND(SUM(total_amount)) FROM orders WHERE status = 'completed'",
    }
    for name, q in stats.items():
        value = conn.execute(q).fetchone()[0]
        st.metric(name, f"{value:,.0f}")


def render_results() -> None:
    result = st.session_state["result"]
    st.markdown("---")
    tab_data, tab_chart, tab_export = st.tabs(["📋 Results", "📊 Chart", "💾 Export"])

    with tab_data:
        st.dataframe(result, use_container_width=True)

    with tab_chart:
        if len(result.columns) >= 2:
            chart_type = st.selectbox("Chart type", ["Bar", "Line", "Pie", "Scatter", "Area"])
            numeric = result.select_dtypes(include=["number"]).columns.tolist()
            col_x = st.selectbox("X axis", result.columns.tolist(), index=0)
            col_y = st.selectbox(
                "Y axis", numeric or result.columns.tolist(),
                index=min(1, max(len(numeric) - 1, 0)),
            )
            chart_fns = {"Bar": px.bar, "Line": px.line, "Scatter": px.scatter, "Area": px.area}
            try:
                if chart_type == "Pie":
                    fig = px.pie(result, values=col_y, names=col_x)
                else:
                    fig = chart_fns[chart_type](result, x=col_x, y=col_y)
                fig.update_layout(height=420)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not chart this result: {e}")
        else:
            st.info("Need at least 2 columns to chart")

    with tab_export:
        col_a, col_b = st.columns(2)
        with col_a:
            st.download_button("📄 CSV", result.to_csv(index=False),
                               file_name="query_results.csv", mime="text/csv")
        with col_b:
            st.download_button("📋 JSON", result.to_json(orient="records", indent=2),
                               file_name="query_results.json", mime="application/json")
        st.markdown("**Query:**")
        st.code(st.session_state.get("query", ""), language="sql")


def main() -> None:
    st.title("🔍 SQL Query Playground")
    st.markdown("Run SQL against a sample e-commerce database — or start from a tested template.")

    conn = get_connection()
    render_sidebar(conn)

    col_query, col_stats = st.columns([2, 1])
    with col_query:
        render_query_panel(conn)
    with col_stats:
        render_stats(conn)

    if "result" in st.session_state:
        render_results()


if __name__ == "__main__":
    main()
