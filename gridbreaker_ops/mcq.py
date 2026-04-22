from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb

from .common import FAILED_ORDER_STATUSES, run_query, write_csv_rows


@dataclass
class McqResult:
    question_id: str
    metric_name: str
    metric_value: Any
    note: str


def get_q8_method_match_stats(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    rows = run_query(
        con,
        """
        WITH o AS (
            SELECT order_id, lower(trim(payment_method)) AS order_payment_method
            FROM orders
            WHERE payment_method IS NOT NULL
        ),
        p AS (
            SELECT order_id, lower(trim(payment_method)) AS payment_payment_method
            FROM payments
            WHERE payment_method IS NOT NULL
        ),
        joined AS (
            SELECT
                o.order_id,
                o.order_payment_method,
                p.payment_payment_method,
                CASE
                    WHEN o.order_payment_method = p.payment_payment_method THEN 1
                    ELSE 0
                END AS is_match
            FROM o
            INNER JOIN p ON o.order_id = p.order_id
        )
        SELECT
            COUNT(*) AS compared_rows,
            SUM(is_match) AS matched_rows,
            SUM(CASE WHEN is_match = 0 THEN 1 ELSE 0 END) AS mismatched_rows,
            CASE
                WHEN COUNT(*) = 0 THEN NULL
                ELSE SUM(is_match) * 1.0 / COUNT(*)
            END AS match_ratio
        FROM joined
        """,
    )
    return rows[0] if rows else {"compared_rows": 0, "matched_rows": 0, "mismatched_rows": 0, "match_ratio": None}


def solve_mcqs(con: duckdb.DuckDBPyConnection) -> list[McqResult]:
    failed_status_list = ", ".join([f"'{s}'" for s in FAILED_ORDER_STATUSES])
    results: list[McqResult] = []

    q1 = run_query(
        con,
        """
        WITH base AS (
            SELECT
                customer_id,
                CAST(order_date AS DATE) AS order_date,
                LAG(CAST(order_date AS DATE)) OVER (
                    PARTITION BY customer_id
                    ORDER BY CAST(order_date AS DATE)
                ) AS prev_order_date
            FROM orders
        ),
        gaps AS (
            SELECT
                customer_id,
                date_diff('day', prev_order_date, order_date) AS gap_days
            FROM base
            WHERE prev_order_date IS NOT NULL
        )
        SELECT median(gap_days) AS median_inter_order_gap_days
        FROM gaps
        """,
    )
    results.append(McqResult("Q1", "median_inter_order_gap_days", q1[0]["median_inter_order_gap_days"], "LAG over order_date by customer_id"))

    q2 = run_query(
        con,
        """
        SELECT
            segment,
            AVG((price - cogs) / NULLIF(price, 0)) AS avg_margin
        FROM products
        GROUP BY segment
        ORDER BY avg_margin DESC
        LIMIT 1
        """,
    )
    results.append(McqResult("Q2", "highest_margin_segment", q2[0]["segment"], "AVG((price-cogs)/price) by segment"))

    q3 = run_query(
        con,
        """
        SELECT
            r.return_reason,
            COUNT(*) AS freq
        FROM returns r
        INNER JOIN products p ON r.product_id = p.product_id
        WHERE lower(p.category) = 'streetwear'
        GROUP BY r.return_reason
        ORDER BY freq DESC, r.return_reason
        LIMIT 1
        """,
    )
    results.append(McqResult("Q3", "top_streetwear_return_reason", q3[0]["return_reason"], "Mode return_reason after returns-products join"))

    q4 = run_query(
        con,
        """
        SELECT
            traffic_source,
            AVG(bounce_rate) AS avg_bounce_rate
        FROM web_traffic
        GROUP BY traffic_source
        ORDER BY avg_bounce_rate ASC
        LIMIT 1
        """,
    )
    results.append(McqResult("Q4", "lowest_bounce_source", q4[0]["traffic_source"], "Min average bounce_rate by traffic_source"))

    q5 = run_query(
        con,
        """
        SELECT
            SUM(CASE WHEN promo_id IS NOT NULL OR promo_id_2 IS NOT NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS promo_item_ratio
        FROM order_items
        """,
    )
    results.append(McqResult("Q5", "promo_item_ratio", q5[0]["promo_item_ratio"], "Promo applied if promo_id OR promo_id_2 is not null"))

    q6 = run_query(
        con,
        """
        WITH per_customer AS (
            SELECT
                c.customer_id,
                c.age_group,
                COUNT(o.order_id) AS n_orders
            FROM customers c
            LEFT JOIN orders o ON c.customer_id = o.customer_id
            WHERE c.age_group IS NOT NULL
              AND trim(c.age_group) <> ''
            GROUP BY c.customer_id, c.age_group
        )
        SELECT
            age_group,
            AVG(n_orders) AS avg_orders_per_customer
        FROM per_customer
        GROUP BY age_group
        ORDER BY avg_orders_per_customer DESC, age_group
        LIMIT 1
        """,
    )
    results.append(McqResult("Q6", "highest_avg_orders_age_group", q6[0]["age_group"], "Join orders-customers and average orders by valid age_group"))

    q7 = run_query(
        con,
        f"""
        WITH valid_orders AS (
            SELECT order_id, zip
            FROM orders
            WHERE lower(order_status) NOT IN ({failed_status_list})
        ),
        line_revenue AS (
            SELECT
                order_id,
                quantity * unit_price - discount_amount AS revenue_line
            FROM order_items
        )
        SELECT
            COALESCE(g.region, 'Unknown') AS region,
            SUM(lr.revenue_line) AS total_revenue
        FROM valid_orders vo
        INNER JOIN line_revenue lr ON vo.order_id = lr.order_id
        LEFT JOIN geography g ON vo.zip = g.zip
        GROUP BY COALESCE(g.region, 'Unknown')
        ORDER BY total_revenue DESC, region
        LIMIT 1
        """,
    )
    results.append(
        McqResult(
            "Q7",
            "highest_revenue_region",
            q7[0]["region"],
            "Exclude cancelled/returned/failed-like statuses before regional revenue sum",
        )
    )

    q8_match = get_q8_method_match_stats(con)
    match_ratio = q8_match.get("match_ratio")
    use_orders_source = match_ratio == 1.0

    if use_orders_source:
        q8 = run_query(
            con,
            """
            SELECT
                lower(trim(payment_method)) AS payment_method,
                COUNT(*) AS freq
            FROM orders
            WHERE lower(order_status) = 'cancelled'
            GROUP BY lower(trim(payment_method))
            ORDER BY freq DESC, payment_method
            LIMIT 1
            """,
        )
        q8_note = "orders vs payments match 100%, mode computed from orders(cancelled)"
    else:
        q8 = run_query(
            con,
            """
            SELECT
                lower(trim(p.payment_method)) AS payment_method,
                COUNT(*) AS freq
            FROM orders o
            INNER JOIN payments p ON o.order_id = p.order_id
            WHERE lower(o.order_status) = 'cancelled'
            GROUP BY lower(trim(p.payment_method))
            ORDER BY freq DESC, payment_method
            LIMIT 1
            """,
        )
        q8_note = "orders vs payments mismatch detected, mode computed from payments joined to cancelled orders"

    q8_value = q8[0]["payment_method"] if q8 else None
    results.append(McqResult("Q8", "cancelled_orders_mode_payment_method", q8_value, q8_note))
    results.append(
        McqResult(
            "Q8_check",
            "orders_vs_payments_match_ratio",
            match_ratio,
            f"compared_rows={q8_match.get('compared_rows')}, mismatched_rows={q8_match.get('mismatched_rows')}",
        )
    )

    q9 = run_query(
        con,
        """
        WITH order_item_keys AS (
            SELECT DISTINCT order_id, product_id
            FROM order_items
        ),
        ordered_lines AS (
            SELECT
                p.size,
                COUNT(*) AS ordered_line_count
            FROM order_items oi
            INNER JOIN products p ON oi.product_id = p.product_id
            WHERE p.size IN ('S', 'M', 'L', 'XL')
            GROUP BY p.size
        ),
        returned_lines AS (
            SELECT
                p.size,
                COUNT(*) AS returned_line_count
            FROM returns r
            INNER JOIN order_item_keys oik
              ON r.order_id = oik.order_id
             AND r.product_id = oik.product_id
            INNER JOIN products p ON r.product_id = p.product_id
            WHERE p.size IN ('S', 'M', 'L', 'XL')
            GROUP BY p.size
        )
        SELECT
            ol.size,
            COALESCE(rl.returned_line_count, 0) AS returned_line_count,
            ol.ordered_line_count,
            COALESCE(rl.returned_line_count, 0) * 1.0 / NULLIF(ol.ordered_line_count, 0) AS return_rate_by_record
        FROM ordered_lines ol
        LEFT JOIN returned_lines rl ON ol.size = rl.size
        ORDER BY return_rate_by_record DESC, ol.size
        LIMIT 1
        """,
    )
    results.append(
        McqResult(
            "Q9",
            "highest_return_rate_size_by_record_count",
            q9[0]["size"],
            "Return rate defined by record counts, not quantity",
        )
    )

    q10 = run_query(
        con,
        """
        SELECT
            installments,
            AVG(payment_value) AS avg_payment_value
        FROM payments
        GROUP BY installments
        ORDER BY avg_payment_value DESC, installments
        LIMIT 1
        """,
    )
    results.append(McqResult("Q10", "installments_with_highest_avg_payment", q10[0]["installments"], "Max average payment_value by installments"))

    return results


def persist_mcq_results(output_dir: Path, results: list[McqResult]) -> None:
    rows = [
        {
            "question_id": r.question_id,
            "metric_name": r.metric_name,
            "metric_value": r.metric_value,
            "note": r.note,
        }
        for r in results
    ]
    write_csv_rows(output_dir / "mcq_results.csv", rows)
    (output_dir / "mcq_results.json").write_text(
        json.dumps(rows, indent=2, default=str),
        encoding="utf-8",
    )
