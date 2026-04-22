"""
SQL Query Generator & Runner
Interactive SQL query builder with visualization.
"""

import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json

# Page config
st.set_page_config(
    page_title="SQL Query Builder",
    page_icon="🔍",
    layout="wide"
)

# Generate sample database
@st.cache_resource
def create_database():
    """Create in-memory DuckDB with sample e-commerce data."""
    conn = duckdb.connect(':memory:')
    
    # Generate customers
    n_customers = 1000
    countries = ['USA', 'UK', 'Germany', 'France', 'Canada', 'Australia', 'Japan', 'Brazil']
    
    customers = pd.DataFrame({
        'customer_id': range(1, n_customers + 1),
        'email': [f'customer{i}@example.com' for i in range(1, n_customers + 1)],
        'name': [f'Customer {i}' for i in range(1, n_customers + 1)],
        'country': random.choices(countries, weights=[30, 15, 12, 10, 8, 8, 7, 10], k=n_customers),
        'created_at': [datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365)) for _ in range(n_customers)],
        'segment': random.choices(['Premium', 'Standard', 'Basic'], weights=[15, 50, 35], k=n_customers)
    })
    
    # Generate products
    categories = ['Electronics', 'Clothing', 'Home', 'Sports', 'Books', 'Beauty']
    products = pd.DataFrame({
        'product_id': range(1, 101),
        'name': [f'Product {i}' for i in range(1, 101)],
        'category': [categories[(i-1) % 6] for i in range(1, 101)],
        'price': [round(random.uniform(10, 500), 2) for _ in range(100)],
        'cost': [round(random.uniform(5, 200), 2) for _ in range(100)]
    })
    
    # Generate orders
    n_orders = 5000
    orders = pd.DataFrame({
        'order_id': range(1, n_orders + 1),
        'customer_id': [random.randint(1, n_customers) for _ in range(n_orders)],
        'order_date': [datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365), hours=random.randint(0, 23)) for _ in range(n_orders)],
        'status': random.choices(['completed', 'pending', 'cancelled', 'refunded'], weights=[70, 15, 10, 5], k=n_orders),
        'total_amount': [round(random.uniform(20, 500), 2) for _ in range(n_orders)],
        'payment_method': random.choices(['credit_card', 'paypal', 'bank_transfer', 'crypto'], weights=[50, 30, 15, 5], k=n_orders)
    })
    
    # Generate order items
    order_items = []
    for order_id in range(1, n_orders + 1):
        n_items = random.randint(1, 4)
        for _ in range(n_items):
            order_items.append({
                'order_id': order_id,
                'product_id': random.randint(1, 100),
                'quantity': random.randint(1, 3),
                'unit_price': round(random.uniform(10, 300), 2)
            })
    order_items = pd.DataFrame(order_items)
    
    # Register tables
    conn.register('customers', customers)
    conn.register('products', products)
    conn.register('orders', orders)
    conn.register('order_items', order_items)
    
    return conn

# Query templates
QUERY_TEMPLATES = {
    "Revenue Analysis": {
        "description": "Monthly revenue trend",
        "query": """SELECT 
    DATE_TRUNC('month', order_date) as month,
    COUNT(*) as order_count,
    SUM(total_amount) as revenue
FROM orders
WHERE status = 'completed'
GROUP BY 1
ORDER BY 1"""
    },
    "Top Products": {
        "description": "Best selling products by revenue",
        "query": """SELECT 
    p.name,
    p.category,
    SUM(oi.quantity) as units_sold,
    SUM(oi.quantity * oi.unit_price) as revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY 1, 2
ORDER BY 4 DESC
LIMIT 10"""
    },
    "Customer Segments": {
        "description": "Revenue by customer segment",
        "query": """SELECT 
    c.segment,
    COUNT(DISTINCT o.order_id) as orders,
    SUM(o.total_amount) as revenue,
    AVG(o.total_amount) as avg_order_value
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status = 'completed'
GROUP BY 1
ORDER BY 2 DESC"""
    },
    "Country Performance": {
        "description": "Revenue by country",
        "query": """SELECT 
    c.country,
    COUNT(DISTINCT o.order_id) as orders,
    SUM(o.total_amount) as revenue,
    COUNT(DISTINCT c.customer_id) as customers
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status = 'completed'
GROUP BY 1
ORDER BY 3 DESC"""
    },
    "Daily Orders": {
        "description": "Order volume by day",
        "query": """SELECT 
    DATE(order_date) as date,
    COUNT(*) as orders,
    SUM(total_amount) as revenue
FROM orders
GROUP BY 1
ORDER BY 1 DESC
LIMIT 30"""
    },
    "Payment Methods": {
        "description": "Revenue by payment method",
        "query": """SELECT 
    payment_method,
    COUNT(*) as orders,
    SUM(total_amount) as revenue,
    AVG(total_amount) as avg_order
FROM orders
WHERE status = 'completed'
GROUP BY 1
ORDER BY 3 DESC"""
    },
    "Order Status Breakdown": {
        "description": "Distribution of order statuses",
        "query": """SELECT 
    status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage
FROM orders
GROUP BY 1
ORDER BY 2 DESC"""
    },
    "Category Performance": {
        "description": "Revenue by product category",
        "query": """SELECT 
    p.category,
    COUNT(DISTINCT oi.order_id) as orders,
    SUM(oi.quantity) as units,
    SUM(oi.quantity * oi.unit_price) as revenue
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY 1
ORDER BY 4 DESC"""
    }
}

def main():
    st.title("🔍 SQL Query Builder")
    st.markdown("Write, run, and visualize SQL queries interactively.")
    
    # Initialize database
    conn = create_database()
    
    # Sidebar - Schema viewer
    with st.sidebar:
        st.header("📚 Schema")
        st.markdown("### Tables")
        
        tables = ['customers', 'orders', 'products', 'order_items']
        for table in tables:
            with st.expander(f"📦 {table}"):
                # Get table info
                schema = conn.execute(f"DESCRIBE {table}").df()
                st.dataframe(schema, hide_index=True, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 💡 Quick Tips")
        st.markdown("""
        - Use `LIMIT` for large results
        - Join tables with common keys
        - `DATE_TRUNC('month', date)` for monthly grouping
        - `COUNT(DISTINCT x)` for unique counts
        """)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Query input
        st.header("📝 SQL Query")
        
        # Template selector
        template = st.selectbox(
            "Load Template",
            ["Custom"] + list(QUERY_TEMPLATES.keys())
        )
        
        if template != "Custom":
            st.info(f"**{QUERY_TEMPLATES[template]['description']}**")
            default_query = QUERY_TEMPLATES[template]['query']
        else:
            default_query = "SELECT * FROM orders LIMIT 100"
        
        query = st.text_area(
            "SQL Query",
            value=default_query,
            height=200
        )
        
        col_a, col_b = st.columns([1, 4])
        with col_a:
            run_query = st.button("▶ Run Query", type="primary")
        
        if run_query:
            try:
                start_time = datetime.now()
                result = conn.execute(query).df()
                elapsed = (datetime.now() - start_time).total_seconds()
                
                st.success(f"✓ Query executed in {elapsed:.3f}s - {len(result)} rows")
                
                # Store result in session state
                st.session_state['result'] = result
                st.session_state['query'] = query
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    with col2:
        st.header("📊 Quick Stats")
        
        # Show database stats
        stats_queries = {
            "Customers": "SELECT COUNT(*) FROM customers",
            "Orders": "SELECT COUNT(*) FROM orders",
            "Products": "SELECT COUNT(*) FROM products",
            "Total Revenue": "SELECT SUM(total_amount) FROM orders WHERE status = 'completed'"
        }
        
        for name, q in stats_queries.items():
            result = conn.execute(q).fetchone()[0]
            if isinstance(result, float):
                st.metric(name, f"${result:,.0f}")
            else:
                st.metric(name, f"{result:,}")
    
    # Results section
    if 'result' in st.session_state:
        result = st.session_state['result']
        
        st.markdown("---")
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["📋 Results", "📊 Visualization", "💾 Export"])
        
        with tab1:
            st.dataframe(result, use_container_width=True)
        
        with tab2:
            st.subheader("Auto-Generated Charts")
            
            if len(result.columns) >= 2:
                chart_type = st.selectbox(
                    "Chart Type",
                    ["Bar", "Line", "Pie", "Scatter", "Area"]
                )
                
                # Try to auto-detect x and y columns
                numeric_cols = result.select_dtypes(include=['number']).columns.tolist()
                non_numeric_cols = result.select_dtypes(exclude=['number']).columns.tolist()
                
                col_x = st.selectbox("X Axis", result.columns.tolist(), index=0)
                col_y = st.selectbox("Y Axis", numeric_cols if numeric_cols else result.columns.tolist(), index=1 if len(result.columns) > 1 else 0)
                
                try:
                    if chart_type == "Bar":
                        fig = px.bar(result, x=col_x, y=col_y)
                    elif chart_type == "Line":
                        fig = px.line(result, x=col_x, y=col_y)
                    elif chart_type == "Pie":
                        fig = px.pie(result, values=col_y, names=col_x)
                    elif chart_type == "Scatter":
                        fig = px.scatter(result, x=col_x, y=col_y)
                    elif chart_type == "Area":
                        fig = px.area(result, x=col_x, y=col_y)
                    
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not create chart: {str(e)}")
            else:
                st.info("Need at least 2 columns for visualization")
        
        with tab3:
            st.subheader("Export Results")
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                csv = result.to_csv(index=False)
                st.download_button(
                    "📄 Download CSV",
                    csv,
                    file_name="query_results.csv",
                    mime="text/csv"
                )
            
            with col_b:
                json_str = result.to_json(orient='records', indent=2)
                st.download_button(
                    "📋 Download JSON",
                    json_str,
                    file_name="query_results.json",
                    mime="application/json"
                )
            
            with col_c:
                # Query history
                st.markdown("**Query:**")
                st.code(st.session_state.get('query', ''), language='sql')

if __name__ == "__main__":
    main()
