"""Query template library for the SQL playground.

Fundamentals live here; window functions, CTEs, and business analytics are
in ``templates_advanced.py``. ``TEMPLATES`` maps category -> list of
``{name, description, query}`` dicts. Every template is executed against
the sample database by the test suite.
"""

from templates_advanced import ADVANCED_TEMPLATES

_FUNDAMENTALS = {
    "Basics": [
        {
            "name": "Peek at a table",
            "description": "SELECT with LIMIT — always bound your exploratory queries",
            "query": "SELECT * FROM orders LIMIT 10",
        },
        {
            "name": "Sorting",
            "description": "Largest completed orders first",
            "query": """SELECT order_id, customer_id, total_amount, order_date
FROM orders
WHERE status = 'completed'
ORDER BY total_amount DESC
LIMIT 15""",
        },
        {
            "name": "Distinct values",
            "description": "What statuses exist, and how many of each?",
            "query": """SELECT DISTINCT status FROM orders ORDER BY status""",
        },
        {
            "name": "Computed columns",
            "description": "Margin and margin % from price and cost",
            "query": """SELECT name, category, price, cost,
    ROUND(price - cost, 2) AS margin,
    ROUND(100.0 * (price - cost) / price, 1) AS margin_pct
FROM products
ORDER BY margin_pct DESC
LIMIT 15""",
        },
        {
            "name": "Row counts per table",
            "description": "UNION ALL to stack per-table counts",
            "query": """SELECT 'customers' AS table_name, COUNT(*) AS rows FROM customers
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items""",
        },
        {
            "name": "Random sample",
            "description": "DuckDB's USING SAMPLE for quick data inspection",
            "query": "SELECT * FROM customers USING SAMPLE 10 ROWS",
        },
    ],
    "Filtering": [
        {
            "name": "Combining conditions",
            "description": "AND/OR with explicit parentheses",
            "query": """SELECT order_id, total_amount, payment_method
FROM orders
WHERE status = 'completed'
  AND (payment_method = 'credit_card' OR payment_method = 'paypal')
  AND total_amount > 400
ORDER BY total_amount DESC
LIMIT 15""",
        },
        {
            "name": "IN lists",
            "description": "Membership tests instead of chained ORs",
            "query": """SELECT country, COUNT(*) AS customers
FROM customers
WHERE country IN ('UK', 'Germany', 'France')
GROUP BY country
ORDER BY customers DESC""",
        },
        {
            "name": "Date ranges",
            "description": "BETWEEN on timestamps — Q1 2024 orders",
            "query": """SELECT COUNT(*) AS q1_orders, ROUND(SUM(total_amount), 2) AS q1_revenue
FROM orders
WHERE order_date BETWEEN '2024-01-01' AND '2024-03-31 23:59:59'
  AND status = 'completed'""",
        },
        {
            "name": "Pattern matching",
            "description": "LIKE with wildcards",
            "query": """SELECT email, name
FROM customers
WHERE email LIKE 'customer1__@%'
ORDER BY email
LIMIT 15""",
        },
        {
            "name": "Anti-join: customers with no orders",
            "description": "NOT EXISTS — the reliable way to find missing relationships",
            "query": """SELECT c.customer_id, c.name, c.country
FROM customers c
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id)
ORDER BY c.customer_id
LIMIT 20""",
        },
        {
            "name": "CASE bucketing",
            "description": "Label rows into bands, then count the bands",
            "query": """SELECT CASE
        WHEN total_amount < 100 THEN 'small'
        WHEN total_amount < 300 THEN 'medium'
        ELSE 'large'
    END AS order_size,
    COUNT(*) AS orders,
    ROUND(AVG(total_amount), 2) AS avg_amount
FROM orders
GROUP BY 1
ORDER BY avg_amount""",
        },
    ],
    "Joins": [
        {
            "name": "Inner join",
            "description": "Order lines with product names and categories",
            "query": """SELECT oi.order_id, p.name, p.category, oi.quantity, oi.unit_price
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
ORDER BY oi.order_id
LIMIT 15""",
        },
        {
            "name": "Left join with zero-fill",
            "description": "Every customer, including the ones who never ordered",
            "query": """SELECT c.customer_id, c.name,
    COUNT(o.order_id) AS orders,
    COALESCE(ROUND(SUM(o.total_amount), 2), 0) AS total_spend
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id AND o.status = 'completed'
GROUP BY 1, 2
ORDER BY total_spend ASC
LIMIT 15""",
        },
        {
            "name": "Four-table join",
            "description": "Country × category revenue through the full schema",
            "query": """SELECT c.country, p.category,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.status = 'completed'
GROUP BY 1, 2
ORDER BY revenue DESC
LIMIT 20""",
        },
        {
            "name": "Self join",
            "description": "Similar-priced products within the same category",
            "query": """SELECT a.category, a.name AS product_a, b.name AS product_b,
    a.price AS price_a, b.price AS price_b
FROM products a
JOIN products b ON a.category = b.category
    AND a.product_id < b.product_id
    AND ABS(a.price - b.price) < 5
ORDER BY a.category, a.price
LIMIT 15""",
        },
        {
            "name": "Semi join (EXISTS)",
            "description": "Customers who have at least one refunded order",
            "query": """SELECT c.customer_id, c.name, c.segment
FROM customers c
WHERE EXISTS (
    SELECT 1 FROM orders o
    WHERE o.customer_id = c.customer_id AND o.status = 'refunded'
)
ORDER BY c.customer_id
LIMIT 20""",
        },
        {
            "name": "Date spine",
            "description": "generate_series + LEFT JOIN so days without orders still appear",
            "query": """SELECT spine.day, COALESCE(ROUND(SUM(o.total_amount), 2), 0) AS revenue
FROM generate_series(DATE '2024-01-01', DATE '2024-01-14', INTERVAL 1 DAY) AS spine(day)
LEFT JOIN orders o
    ON CAST(o.order_date AS DATE) = spine.day AND o.status = 'completed'
GROUP BY spine.day
ORDER BY spine.day""",
        },
        {
            "name": "Join vs join-with-filter",
            "description": "Filter inside the ON clause keeps unmatched rows",
            "query": """SELECT c.segment,
    COUNT(DISTINCT c.customer_id) AS all_customers,
    COUNT(DISTINCT o.customer_id) AS crypto_payers
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id AND o.payment_method = 'crypto'
GROUP BY 1
ORDER BY all_customers DESC""",
        },
    ],
    "Aggregation": [
        {
            "name": "GROUP BY + HAVING",
            "description": "HAVING filters groups after aggregation",
            "query": """SELECT country, COUNT(*) AS customers
FROM customers
GROUP BY country
HAVING COUNT(*) > 100
ORDER BY customers DESC""",
        },
        {
            "name": "The full aggregate set",
            "description": "COUNT/SUM/AVG/MIN/MAX in one pass",
            "query": """SELECT status,
    COUNT(*) AS orders,
    ROUND(SUM(total_amount), 2) AS revenue,
    ROUND(AVG(total_amount), 2) AS avg_value,
    MIN(total_amount) AS smallest,
    MAX(total_amount) AS largest
FROM orders
GROUP BY status
ORDER BY revenue DESC""",
        },
        {
            "name": "Conditional aggregation (FILTER)",
            "description": "Pivot statuses into columns without a PIVOT clause",
            "query": """SELECT payment_method,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed,
    COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled,
    COUNT(*) FILTER (WHERE status = 'refunded')  AS refunded
FROM orders
GROUP BY 1
ORDER BY completed DESC""",
        },
        {
            "name": "ROLLUP subtotals",
            "description": "Per-group rows plus subtotal and grand-total rows",
            "query": """SELECT c.country, c.segment, ROUND(SUM(o.total_amount), 2) AS revenue
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
WHERE o.status = 'completed'
GROUP BY ROLLUP (c.country, c.segment)
ORDER BY c.country NULLS LAST, c.segment NULLS LAST""",
        },
        {
            "name": "Median and percentiles",
            "description": "PERCENTILE_CONT for distribution shape, not just averages",
            "query": """SELECT status,
    ROUND(AVG(total_amount), 2) AS mean,
    PERCENTILE_CONT(0.5)  WITHIN GROUP (ORDER BY total_amount) AS median,
    PERCENTILE_CONT(0.9)  WITHIN GROUP (ORDER BY total_amount) AS p90
FROM orders
GROUP BY status""",
        },
        {
            "name": "String aggregation",
            "description": "STRING_AGG collapses a group into one readable cell",
            "query": """SELECT oi.order_id,
    STRING_AGG(DISTINCT p.category, ', ' ORDER BY p.category) AS categories_in_order
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY oi.order_id
ORDER BY oi.order_id
LIMIT 12""",
        },
        {
            "name": "Distinct counts",
            "description": "COUNT(DISTINCT ...) — unique buyers per payment method",
            "query": """SELECT payment_method,
    COUNT(*) AS orders,
    COUNT(DISTINCT customer_id) AS unique_buyers
FROM orders
GROUP BY 1
ORDER BY orders DESC""",
        },
    ],
    "Date & Time": [
        {
            "name": "Monthly revenue",
            "description": "DATE_TRUNC is the workhorse of time-series SQL",
            "query": """SELECT DATE_TRUNC('month', order_date) AS month,
    COUNT(*) AS orders,
    ROUND(SUM(total_amount), 2) AS revenue
FROM orders
WHERE status = 'completed'
GROUP BY 1
ORDER BY 1""",
        },
        {
            "name": "Day-of-week pattern",
            "description": "Which weekdays sell the most?",
            "query": """SELECT DAYNAME(order_date) AS weekday,
    COUNT(*) AS orders,
    ROUND(AVG(total_amount), 2) AS avg_value
FROM orders
GROUP BY weekday, DAYOFWEEK(order_date)
ORDER BY DAYOFWEEK(order_date)""",
        },
        {
            "name": "Hour-of-day distribution",
            "description": "EXTRACT pulls any date part",
            "query": """SELECT EXTRACT(hour FROM order_date) AS hour, COUNT(*) AS orders
FROM orders
GROUP BY 1
ORDER BY 1""",
        },
        {
            "name": "Signup-to-first-order gap",
            "description": "DATE_DIFF between two event dates per customer",
            "query": """SELECT c.customer_id, c.created_at,
    MIN(o.order_date) AS first_order,
    DATE_DIFF('day', c.created_at, MIN(o.order_date)) AS days_to_first_order
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
GROUP BY 1, 2
HAVING DATE_DIFF('day', c.created_at, MIN(o.order_date)) >= 0
ORDER BY days_to_first_order
LIMIT 15""",
        },
        {
            "name": "Quarterly summary",
            "description": "QUARTER() for coarse-grained reporting",
            "query": """SELECT QUARTER(order_date) AS quarter,
    COUNT(*) AS orders,
    ROUND(SUM(total_amount), 2) AS revenue
FROM orders
WHERE status = 'completed'
GROUP BY 1
ORDER BY 1""",
        },
        {
            "name": "Signup cohort sizes",
            "description": "Customers grouped by signup month",
            "query": """SELECT DATE_TRUNC('month', created_at) AS signup_month,
    COUNT(*) AS new_customers,
    SUM(COUNT(*)) OVER (ORDER BY DATE_TRUNC('month', created_at)) AS running_total
FROM customers
GROUP BY 1
ORDER BY 1""",
        },
    ],
}

TEMPLATES = {**_FUNDAMENTALS, **ADVANCED_TEMPLATES}


def all_templates():
    """Yield (category, template) for every template in the library."""
    for category, templates in TEMPLATES.items():
        for template in templates:
            yield category, template


def template_count() -> int:
    return sum(len(templates) for templates in TEMPLATES.values())
