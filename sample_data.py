"""Deterministic sample e-commerce database for the SQL playground.

Builds an in-memory DuckDB with four related tables. The RNG is seeded, so
every run (and the test suite) sees identical data.

    customers(customer_id, email, name, country, created_at, segment)
    products(product_id, name, category, price, cost)
    orders(order_id, customer_id, order_date, status, total_amount, payment_method)
    order_items(order_id, product_id, quantity, unit_price)
"""

import random
from datetime import datetime, timedelta

import duckdb
import pandas as pd

SEED = 42
N_CUSTOMERS = 1000
N_PRODUCTS = 100
N_ORDERS = 5000

COUNTRIES = ["USA", "UK", "Germany", "France", "Canada", "Australia", "Japan", "Brazil"]
CATEGORIES = ["Electronics", "Clothing", "Home", "Sports", "Books", "Beauty"]
TABLES = ("customers", "products", "orders", "order_items")


def create_database() -> duckdb.DuckDBPyConnection:
    """Return an in-memory DuckDB connection with the sample tables registered."""
    rng = random.Random(SEED)
    conn = duckdb.connect(":memory:")

    customers = pd.DataFrame({
        "customer_id": range(1, N_CUSTOMERS + 1),
        "email": [f"customer{i}@example.com" for i in range(1, N_CUSTOMERS + 1)],
        "name": [f"Customer {i}" for i in range(1, N_CUSTOMERS + 1)],
        "country": rng.choices(COUNTRIES, weights=[30, 15, 12, 10, 8, 8, 7, 10], k=N_CUSTOMERS),
        "created_at": [datetime(2024, 1, 1) + timedelta(days=rng.randint(0, 365)) for _ in range(N_CUSTOMERS)],
        "segment": rng.choices(["Premium", "Standard", "Basic"], weights=[15, 50, 35], k=N_CUSTOMERS),
    })

    products = pd.DataFrame({
        "product_id": range(1, N_PRODUCTS + 1),
        "name": [f"Product {i}" for i in range(1, N_PRODUCTS + 1)],
        "category": [CATEGORIES[(i - 1) % len(CATEGORIES)] for i in range(1, N_PRODUCTS + 1)],
        "price": [round(rng.uniform(10, 500), 2) for _ in range(N_PRODUCTS)],
        "cost": [round(rng.uniform(5, 200), 2) for _ in range(N_PRODUCTS)],
    })

    orders = pd.DataFrame({
        "order_id": range(1, N_ORDERS + 1),
        "customer_id": [rng.randint(1, N_CUSTOMERS) for _ in range(N_ORDERS)],
        "order_date": [
            datetime(2024, 1, 1) + timedelta(days=rng.randint(0, 365), hours=rng.randint(0, 23))
            for _ in range(N_ORDERS)
        ],
        "status": rng.choices(["completed", "pending", "cancelled", "refunded"], weights=[70, 15, 10, 5], k=N_ORDERS),
        "total_amount": [round(rng.uniform(20, 500), 2) for _ in range(N_ORDERS)],
        "payment_method": rng.choices(["credit_card", "paypal", "bank_transfer", "crypto"], weights=[50, 30, 15, 5], k=N_ORDERS),
    })

    items = []
    for order_id in range(1, N_ORDERS + 1):
        for _ in range(rng.randint(1, 4)):
            items.append({
                "order_id": order_id,
                "product_id": rng.randint(1, N_PRODUCTS),
                "quantity": rng.randint(1, 3),
                "unit_price": round(rng.uniform(10, 300), 2),
            })
    order_items = pd.DataFrame(items)

    conn.register("customers", customers)
    conn.register("products", products)
    conn.register("orders", orders)
    conn.register("order_items", order_items)
    return conn
