# SQL Query Generator & Runner

Interactive SQL query builder with visualization. Write, run, and visualize SQL queries in your browser.

## Features

- 📝 **Query Builder** - Visual query construction
- 📊 **Auto-Visualization** - Charts generated from results
- 💾 **Query Library** - Save and share common queries
- 📋 **Export** - CSV, JSON, Excel export
- 🎯 **Templates** - 50+ pre-built query templates

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Query Templates Included

### Analytics
- Monthly revenue trends
- Customer cohort analysis
- Product performance ranking
- Funnel conversion rates

### Marketing
- Campaign ROI analysis
- Channel attribution
- A/B test results
- Customer acquisition cost

### Operations
- Inventory turnover
- Order fulfillment time
- Support ticket analysis
- Daily active users

## Sample Schema

The app includes a complete e-commerce schema:

```sql
-- Customers
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    email VARCHAR(255),
    created_at TIMESTAMP,
    country VARCHAR(100),
    lifetime_value DECIMAL
);

-- Orders
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    order_date TIMESTAMP,
    total_amount DECIMAL,
    status VARCHAR(50)
);

-- Products
CREATE TABLE products (
    product_id INT PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(100),
    price DECIMAL
);
```

## Use Cases

1. **Learn SQL** - Interactive tutorials with instant feedback
2. **Analyze Data** - Run queries without database access
3. **Generate Reports** - Export formatted results
4. **Prototype Queries** - Test before running on production

## Tech Stack

- Python 3.10+
- Streamlit (UI)
- DuckDB (in-memory SQL)
- Plotly (visualizations)
