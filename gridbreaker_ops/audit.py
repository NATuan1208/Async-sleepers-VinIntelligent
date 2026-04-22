from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb

from .common import FAILED_ORDER_STATUSES, run_query, write_csv_rows


def build_audit_queries() -> dict[str, str]:
    failed_status_list = ", ".join([f"'{s}'" for s in FAILED_ORDER_STATUSES])
    return {
        "sales_missing_dates_count": """
            WITH bounds AS (
                SELECT MIN(CAST(Date AS DATE)) AS min_date,
                       MAX(CAST(Date AS DATE)) AS max_date
                FROM sales
            ),
            all_dates AS (
                SELECT *
                FROM generate_series(
                    (SELECT min_date FROM bounds),
                    (SELECT max_date FROM bounds),
                    INTERVAL 1 DAY
                ) AS t(expected_date)
            )
            SELECT COUNT(*) AS missing_dates
            FROM all_dates d
            LEFT JOIN sales s
              ON CAST(s.Date AS DATE) = d.expected_date
            WHERE s.Date IS NULL
        """,
        "sales_missing_dates_detail": """
            WITH bounds AS (
                SELECT MIN(CAST(Date AS DATE)) AS min_date,
                       MAX(CAST(Date AS DATE)) AS max_date
                FROM sales
            ),
            all_dates AS (
                SELECT *
                FROM generate_series(
                    (SELECT min_date FROM bounds),
                    (SELECT max_date FROM bounds),
                    INTERVAL 1 DAY
                ) AS t(expected_date)
            )
            SELECT d.expected_date AS missing_date
            FROM all_dates d
            LEFT JOIN sales s
              ON CAST(s.Date AS DATE) = d.expected_date
            WHERE s.Date IS NULL
            ORDER BY d.expected_date
        """,
        "orphan_order_items_product": """
            SELECT COUNT(*) AS orphan_rows
            FROM order_items oi
            LEFT JOIN products p ON oi.product_id = p.product_id
            WHERE p.product_id IS NULL
        """,
        "orphan_order_items_order": """
            SELECT COUNT(*) AS orphan_rows
            FROM order_items oi
            LEFT JOIN orders o ON oi.order_id = o.order_id
            WHERE o.order_id IS NULL
        """,
        "orphan_orders_customer": """
            SELECT COUNT(*) AS orphan_rows
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.customer_id
            WHERE c.customer_id IS NULL
        """,
        "orphan_orders_zip": """
            SELECT COUNT(*) AS orphan_rows
            FROM orders o
            LEFT JOIN geography g ON o.zip = g.zip
            WHERE g.zip IS NULL
        """,
        "orphan_returns_item_key": """
            SELECT COUNT(*) AS orphan_rows
            FROM returns r
            LEFT JOIN order_items oi
              ON r.order_id = oi.order_id
             AND r.product_id = oi.product_id
            WHERE oi.order_id IS NULL
        """,
        "business_logic_cogs_ge_price": """
            SELECT COUNT(*) AS violation_rows
            FROM products
            WHERE cogs >= price
        """,
        "null_blank_age_group": """
            SELECT COUNT(*) AS null_or_blank_rows
            FROM customers
            WHERE age_group IS NULL OR trim(age_group) = ''
        """,
        "promo_null_and_applied_ratio": """
            SELECT
                COUNT(*) AS total_rows,
                SUM(CASE WHEN promo_id IS NULL THEN 1 ELSE 0 END) AS promo_id_null_rows,
                SUM(CASE WHEN promo_id_2 IS NULL THEN 1 ELSE 0 END) AS promo_id_2_null_rows,
                SUM(CASE WHEN promo_id IS NOT NULL OR promo_id_2 IS NOT NULL THEN 1 ELSE 0 END) AS promo_applied_rows,
                SUM(CASE WHEN promo_id IS NOT NULL OR promo_id_2 IS NOT NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS promo_applied_ratio
            FROM order_items
        """,
        "duplicate_orders_order_id": """
            SELECT COUNT(*) AS duplicated_keys
            FROM (
                SELECT order_id
                FROM orders
                GROUP BY order_id
                HAVING COUNT(*) > 1
            ) t
        """,
        "duplicate_customers_customer_id": """
            SELECT COUNT(*) AS duplicated_keys
            FROM (
                SELECT customer_id
                FROM customers
                GROUP BY customer_id
                HAVING COUNT(*) > 1
            ) t
        """,
        "duplicate_products_product_id": """
            SELECT COUNT(*) AS duplicated_keys
            FROM (
                SELECT product_id
                FROM products
                GROUP BY product_id
                HAVING COUNT(*) > 1
            ) t
        """,
        "duplicate_order_items_natural_key": """
            SELECT COUNT(*) AS duplicated_keys
            FROM (
                SELECT order_id, product_id, promo_id, promo_id_2
                FROM order_items
                GROUP BY order_id, product_id, promo_id, promo_id_2
                HAVING COUNT(*) > 1
            ) t
        """,
        "negative_values_sanity": """
            SELECT
                SUM(CASE WHEN quantity < 0 THEN 1 ELSE 0 END) AS negative_quantity_rows,
                SUM(CASE WHEN unit_price < 0 THEN 1 ELSE 0 END) AS negative_unit_price_rows,
                (SELECT SUM(CASE WHEN payment_value < 0 THEN 1 ELSE 0 END) FROM payments) AS negative_payment_rows,
                (SELECT SUM(CASE WHEN return_quantity < 0 THEN 1 ELSE 0 END) FROM returns) AS negative_return_qty_rows
            FROM order_items
        """,
        "cancelled_returned_order_ratio": f"""
            SELECT
                COUNT(*) AS total_orders,
                SUM(CASE WHEN lower(order_status) IN ({failed_status_list}) THEN 1 ELSE 0 END) AS failed_like_orders,
                SUM(CASE WHEN lower(order_status) IN ({failed_status_list}) THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS failed_like_ratio
            FROM orders
        """,
        "payment_method_return_rate_baseline": """
            WITH order_return_flag AS (
                SELECT
                    o.order_id,
                    lower(trim(o.payment_method)) AS payment_method,
                    CASE WHEN r.order_id IS NULL THEN 0 ELSE 1 END AS is_returned
                FROM orders o
                LEFT JOIN (
                    SELECT DISTINCT order_id
                    FROM returns
                ) r ON o.order_id = r.order_id
            )
            SELECT
                payment_method,
                COUNT(*) AS order_count,
                AVG(is_returned) AS return_rate
            FROM order_return_flag
            GROUP BY payment_method
            ORDER BY return_rate DESC, order_count DESC
        """,
    }


def run_audit_pack(con: duckdb.DuckDBPyConnection, output_dir: Path) -> dict[str, list[dict[str, Any]]]:
    queries = build_audit_queries()
    results: dict[str, list[dict[str, Any]]] = {}

    for name, sql in queries.items():
        rows = run_query(con, sql)
        results[name] = rows

    (output_dir / "audit_results.json").write_text(
        json.dumps(results, indent=2, default=str),
        encoding="utf-8",
    )

    write_csv_rows(output_dir / "audit_sales_missing_dates.csv", results.get("sales_missing_dates_detail", []))
    write_csv_rows(
        output_dir / "audit_payment_method_return_rate.csv",
        results.get("payment_method_return_rate_baseline", []),
    )

    summary_rows: list[dict[str, Any]] = []
    for check_name, rows in results.items():
        if len(rows) == 1:
            single_row = rows[0]
            summary_rows.append(
                {
                    "check_name": check_name,
                    "result": json.dumps(single_row, default=str),
                }
            )
    write_csv_rows(output_dir / "audit_summary.csv", summary_rows)

    return results
