-- Act 2: Year-by-year leak breakdown for stacked bar chart (Chart 2.2)
-- All 5 leak types + true remaining per year

WITH years AS (
    SELECT EXTRACT(year FROM Date)::INT AS year, SUM(Revenue) AS gross_revenue
    FROM sales
    GROUP BY year
),
discount_by_year AS (
    SELECT EXTRACT(year FROM o.order_date)::INT AS year,
           SUM(oi.discount_amount)               AS discount_cost
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    GROUP BY year
),
return_by_year AS (
    SELECT EXTRACT(year FROM return_date)::INT AS year,
           SUM(refund_amount)                   AS return_cost
    FROM returns
    GROUP BY year
),
shipping_by_year AS (
    SELECT EXTRACT(year FROM o.order_date)::INT AS year,
           SUM(s.shipping_fee)                   AS shipping_absorbed
    FROM orders o
    JOIN shipments s ON o.order_id = s.order_id
    WHERE o.order_status = 'cancelled'
    GROUP BY year
),
stockout_by_year AS (
    WITH inv AS (
        SELECT i.year, i.month, i.product_id, i.units_sold, i.stockout_days,
               DATE_DIFF('day',
                   MAKE_DATE(i.year::INT, i.month::INT, 1),
                   (MAKE_DATE(i.year::INT, i.month::INT, 1) + INTERVAL 1 MONTH)
               ) AS days_in_month, p.price
        FROM inventory i JOIN products p ON i.product_id = p.product_id
        WHERE i.stockout_days > 0
    ),
    demand AS (
        SELECT *, GREATEST(days_in_month - stockout_days, 1) AS selling_days,
               units_sold / GREATEST(days_in_month - stockout_days, 1) AS avg_daily_demand
        FROM inv
    )
    SELECT year,
           SUM(LEAST(avg_daily_demand * 2, avg_daily_demand * 2) * stockout_days * price) AS phantom_revenue
    FROM demand
    GROUP BY year
)
SELECT
    y.year,
    y.gross_revenue,
    COALESCE(d.discount_cost,     0) AS discount_cost,
    COALESCE(r.return_cost,       0) AS return_cost,
    COALESCE(sh.shipping_absorbed,0) AS shipping_absorbed,
    COALESCE(st.phantom_revenue,  0) AS phantom_revenue,
    y.gross_revenue
        - COALESCE(d.discount_cost,     0)
        - COALESCE(r.return_cost,       0)
        - COALESCE(sh.shipping_absorbed,0)
        - COALESCE(st.phantom_revenue,  0) AS true_remaining
FROM years y
LEFT JOIN discount_by_year  d  ON y.year = d.year
LEFT JOIN return_by_year     r  ON y.year = r.year
LEFT JOIN shipping_by_year   sh ON y.year = sh.year
LEFT JOIN stockout_by_year   st ON y.year = st.year
ORDER BY y.year;
