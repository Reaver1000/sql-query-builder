"""Advanced template categories: window functions, CTEs, business analytics.

Merged into the full library by ``templates.py``.
"""

ADVANCED_TEMPLATES = {
    "Window Functions": [
        {
            "name": "Latest order per customer",
            "description": "ROW_NUMBER + QUALIFY to keep one row per group",
            "query": """SELECT customer_id, order_id, order_date, total_amount
FROM orders
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) = 1
ORDER BY customer_id
LIMIT 20""",
        },
        {
            "name": "Product rank within category",
            "description": "RANK and DENSE_RANK compared side by side",
            "query": """SELECT p.category, p.name,
    SUM(oi.quantity * oi.unit_price) AS revenue,
    RANK()       OVER (PARTITION BY p.category ORDER BY SUM(oi.quantity * oi.unit_price) DESC) AS rnk,
    DENSE_RANK() OVER (PARTITION BY p.category ORDER BY SUM(oi.quantity * oi.unit_price) DESC) AS dense_rnk
FROM products p
JOIN order_items oi ON oi.product_id = p.product_id
GROUP BY p.category, p.name
QUALIFY rnk <= 3
ORDER BY p.category, rnk""",
        },
        {
            "name": "Running revenue total",
            "description": "Cumulative sum over ordered daily revenue",
            "query": """WITH daily AS (
    SELECT CAST(order_date AS DATE) AS day, SUM(total_amount) AS revenue
    FROM orders WHERE status = 'completed' GROUP BY 1
)
SELECT day, revenue,
    SUM(revenue) OVER (ORDER BY day) AS cumulative_revenue
FROM daily
ORDER BY day
LIMIT 31""",
        },
        {
            "name": "7-day moving average",
            "description": "Window frame: ROWS BETWEEN 6 PRECEDING AND CURRENT ROW",
            "query": """WITH daily AS (
    SELECT CAST(order_date AS DATE) AS day, SUM(total_amount) AS revenue
    FROM orders WHERE status = 'completed' GROUP BY 1
)
SELECT day, revenue,
    ROUND(AVG(revenue) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS ma_7d
FROM daily
ORDER BY day
LIMIT 31""",
        },
        {
            "name": "Month-over-month growth",
            "description": "LAG to compare each month with the previous one",
            "query": """WITH monthly AS (
    SELECT DATE_TRUNC('month', order_date) AS month, SUM(total_amount) AS revenue
    FROM orders WHERE status = 'completed' GROUP BY 1
)
SELECT month, revenue,
    LAG(revenue) OVER (ORDER BY month) AS prev_month,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
          / NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 1) AS growth_pct
FROM monthly
ORDER BY month""",
        },
        {
            "name": "Customer spend quartiles",
            "description": "NTILE(4) buckets customers by total spend",
            "query": """WITH spend AS (
    SELECT customer_id, SUM(total_amount) AS total_spend
    FROM orders WHERE status = 'completed' GROUP BY 1
), tiled AS (
    SELECT customer_id, total_spend,
        NTILE(4) OVER (ORDER BY total_spend) AS quartile
    FROM spend
)
SELECT quartile,
    COUNT(*) AS customers,
    ROUND(MIN(total_spend), 2) AS min_spend,
    ROUND(AVG(total_spend), 2) AS avg_spend,
    ROUND(MAX(total_spend), 2) AS max_spend
FROM tiled
GROUP BY quartile
ORDER BY quartile""",
        },
        {
            "name": "Share of total revenue",
            "description": "SUM() OVER () with no partition = grand total",
            "query": """SELECT p.category,
    SUM(oi.quantity * oi.unit_price) AS revenue,
    ROUND(100.0 * SUM(oi.quantity * oi.unit_price) / SUM(SUM(oi.quantity * oi.unit_price)) OVER (), 1) AS pct_of_total
FROM products p
JOIN order_items oi ON oi.product_id = p.product_id
GROUP BY p.category
ORDER BY revenue DESC""",
        },
        {
            "name": "First and latest order per customer",
            "description": "MIN/MAX as window functions preserve detail rows",
            "query": """SELECT DISTINCT customer_id,
    MIN(order_date) OVER (PARTITION BY customer_id) AS first_order,
    MAX(order_date) OVER (PARTITION BY customer_id) AS latest_order
FROM orders
ORDER BY customer_id
LIMIT 20""",
        },
    ],
    "CTEs & Subqueries": [
        {
            "name": "CTE: high-value customers",
            "description": "Name an intermediate result, then join against it",
            "query": """WITH big_spenders AS (
    SELECT customer_id, SUM(total_amount) AS spend
    FROM orders WHERE status = 'completed'
    GROUP BY 1
    HAVING SUM(total_amount) > 1500
)
SELECT c.name, c.country, c.segment, b.spend
FROM big_spenders b
JOIN customers c ON c.customer_id = b.customer_id
ORDER BY b.spend DESC
LIMIT 20""",
        },
        {
            "name": "Multi-CTE funnel",
            "description": "Chained CTEs: base revenue → country totals → top 3",
            "query": """WITH completed AS (
    SELECT * FROM orders WHERE status = 'completed'
), by_country AS (
    SELECT c.country, SUM(o.total_amount) AS revenue
    FROM completed o JOIN customers c ON c.customer_id = o.customer_id
    GROUP BY 1
)
SELECT * FROM by_country ORDER BY revenue DESC LIMIT 3""",
        },
        {
            "name": "Orders above the customer's own average",
            "description": "Correlated subquery — re-evaluated per outer row",
            "query": """SELECT o.customer_id, o.order_id, o.total_amount
FROM orders o
WHERE o.status = 'completed'
  AND o.total_amount > 1.8 * (
      SELECT AVG(o2.total_amount) FROM orders o2
      WHERE o2.customer_id = o.customer_id AND o2.status = 'completed'
  )
ORDER BY o.total_amount DESC
LIMIT 20""",
        },
        {
            "name": "Orders vs global average",
            "description": "Scalar subquery used inline in an expression",
            "query": """SELECT order_id, total_amount,
    ROUND(total_amount - (SELECT AVG(total_amount) FROM orders WHERE status = 'completed'), 2) AS vs_avg
FROM orders
WHERE status = 'completed'
ORDER BY vs_avg DESC
LIMIT 15""",
        },
        {
            "name": "Recursive CTE: month spine",
            "description": "WITH RECURSIVE generating the 12 months of 2024",
            "query": """WITH RECURSIVE months(month_start) AS (
    SELECT DATE '2024-01-01'
    UNION ALL
    SELECT month_start + INTERVAL 1 MONTH FROM months
    WHERE month_start < DATE '2024-12-01'
)
SELECT m.month_start,
    COALESCE(SUM(o.total_amount), 0) AS revenue
FROM months m
LEFT JOIN orders o
    ON DATE_TRUNC('month', o.order_date) = m.month_start AND o.status = 'completed'
GROUP BY 1
ORDER BY 1""",
        },
        {
            "name": "IN with a subquery",
            "description": "Customers from the single top revenue country",
            "query": """SELECT name, email, segment
FROM customers
WHERE country IN (
    SELECT c.country
    FROM customers c JOIN orders o ON o.customer_id = c.customer_id
    WHERE o.status = 'completed'
    GROUP BY c.country
    ORDER BY SUM(o.total_amount) DESC
    LIMIT 1
)
LIMIT 20""",
        },
    ],
    "Business Analytics": [
        {
            "name": "Pareto (80/20) analysis",
            "description": "Cumulative revenue share — how few products drive most revenue",
            "query": """WITH product_revenue AS (
    SELECT p.name, SUM(oi.quantity * oi.unit_price) AS revenue
    FROM products p JOIN order_items oi ON oi.product_id = p.product_id
    GROUP BY 1
)
SELECT name, revenue,
    ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC) / SUM(revenue) OVER (), 1) AS cumulative_pct
FROM product_revenue
ORDER BY revenue DESC
LIMIT 25""",
        },
        {
            "name": "RFM scores",
            "description": "Recency / Frequency / Monetary quintiles per customer",
            "query": """WITH per_customer AS (
    SELECT customer_id,
        MAX(order_date) AS last_order,
        COUNT(*) AS frequency,
        SUM(total_amount) AS monetary
    FROM orders WHERE status = 'completed'
    GROUP BY 1
)
SELECT customer_id,
    NTILE(5) OVER (ORDER BY last_order)  AS r_score,
    NTILE(5) OVER (ORDER BY frequency)   AS f_score,
    NTILE(5) OVER (ORDER BY monetary)    AS m_score,
    frequency, ROUND(monetary, 2) AS monetary
FROM per_customer
ORDER BY monetary DESC
LIMIT 20""",
        },
        {
            "name": "Cohort retention",
            "description": "Signup cohort vs months-to-order matrix (FILTER pivots)",
            "query": """WITH cohorts AS (
    SELECT c.customer_id, DATE_TRUNC('month', c.created_at) AS cohort_month
    FROM customers c
), activity AS (
    SELECT ch.cohort_month,
        DATE_DIFF('month', ch.cohort_month, DATE_TRUNC('month', o.order_date)) AS month_offset,
        o.customer_id
    FROM cohorts ch JOIN orders o ON o.customer_id = ch.customer_id
    WHERE o.status = 'completed'
)
SELECT cohort_month,
    COUNT(DISTINCT customer_id) FILTER (WHERE month_offset = 0) AS m0,
    COUNT(DISTINCT customer_id) FILTER (WHERE month_offset = 1) AS m1,
    COUNT(DISTINCT customer_id) FILTER (WHERE month_offset = 2) AS m2,
    COUNT(DISTINCT customer_id) FILTER (WHERE month_offset = 3) AS m3
FROM activity
GROUP BY 1
ORDER BY 1""",
        },
        {
            "name": "Repeat purchase rate",
            "description": "Share of customers with two or more completed orders",
            "query": """WITH order_counts AS (
    SELECT customer_id, COUNT(*) AS n
    FROM orders WHERE status = 'completed'
    GROUP BY 1
)
SELECT COUNT(*) AS buyers,
    COUNT(*) FILTER (WHERE n >= 2) AS repeat_buyers,
    ROUND(100.0 * COUNT(*) FILTER (WHERE n >= 2) / COUNT(*), 1) AS repeat_rate_pct
FROM order_counts""",
        },
        {
            "name": "Average order value trend",
            "description": "Monthly AOV with order counts for context",
            "query": """SELECT DATE_TRUNC('month', order_date) AS month,
    COUNT(*) AS orders,
    ROUND(AVG(total_amount), 2) AS avg_order_value
FROM orders
WHERE status = 'completed'
GROUP BY 1
ORDER BY 1""",
        },
        {
            "name": "Revenue per customer by segment",
            "description": "A simple lifetime-value proxy per segment",
            "query": """SELECT c.segment,
    COUNT(DISTINCT c.customer_id) AS customers,
    ROUND(SUM(o.total_amount), 2) AS revenue,
    ROUND(SUM(o.total_amount) / COUNT(DISTINCT c.customer_id), 2) AS revenue_per_customer
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id AND o.status = 'completed'
GROUP BY 1
ORDER BY revenue_per_customer DESC""",
        },
        {
            "name": "Products bought together",
            "description": "Market-basket pairs via a self join on order_id",
            "query": """SELECT p1.name AS product_a, p2.name AS product_b, COUNT(*) AS times_together
FROM order_items a
JOIN order_items b ON a.order_id = b.order_id AND a.product_id < b.product_id
JOIN products p1 ON p1.product_id = a.product_id
JOIN products p2 ON p2.product_id = b.product_id
GROUP BY 1, 2
ORDER BY times_together DESC
LIMIT 10""",
        },
        {
            "name": "Refund rate by category",
            "description": "Conditional aggregation across joined tables",
            "query": """SELECT p.category,
    COUNT(DISTINCT o.order_id) AS orders,
    COUNT(DISTINCT o.order_id) FILTER (WHERE o.status = 'refunded') AS refunded,
    ROUND(100.0 * COUNT(DISTINCT o.order_id) FILTER (WHERE o.status = 'refunded')
          / COUNT(DISTINCT o.order_id), 2) AS refund_rate_pct
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p ON p.product_id = oi.product_id
GROUP BY 1
ORDER BY refund_rate_pct DESC""",
        },
        {
            "name": "New vs returning revenue",
            "description": "Classify each order against the customer's first order month",
            "query": """WITH firsts AS (
    SELECT customer_id, MIN(DATE_TRUNC('month', order_date)) AS first_month
    FROM orders WHERE status = 'completed' GROUP BY 1
)
SELECT DATE_TRUNC('month', o.order_date) AS month,
    ROUND(SUM(o.total_amount) FILTER (WHERE DATE_TRUNC('month', o.order_date) = f.first_month), 2) AS new_customer_revenue,
    ROUND(SUM(o.total_amount) FILTER (WHERE DATE_TRUNC('month', o.order_date) > f.first_month), 2) AS returning_revenue
FROM orders o
JOIN firsts f ON f.customer_id = o.customer_id
WHERE o.status = 'completed'
GROUP BY 1
ORDER BY 1""",
        },
    ],
}
