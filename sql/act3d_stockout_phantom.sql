-- Act 3D: The Stockout Phantom (CORRECTED)
--
-- CORRECTION FROM ACT 2: Act 2 used LEAST(avg_daily_demand*2, avg_daily_demand*2)
-- which was a tautology — both args identical → always 2x demand (inflated).
-- This query uses 1x avg_daily_demand as base, and shows 2x as upper-bound cap column.
--
-- Methodology:
--   1. avg_daily_demand = units_sold / max(days_in_month - stockout_days, 1)
--   2. phantom_1x = avg_daily_demand × stockout_days × price  (conservative base)
--   3. phantom_2x = phantom_1x × 2                           (upper bound cap)
--   4. Only rows with stockout_days > 0
--
-- Act 2 reported phantom = 890 triệu VND (2x); corrected 1x ≈ 445 triệu VND

-- 1. Corrected phantom by category
WITH inv AS (
    SELECT
        i.product_id, i.year, i.month, i.units_sold, i.stockout_days,
        p.category, p.price,
        DATE_DIFF('day',
            MAKE_DATE(i.year::INT, i.month::INT, 1),
            (MAKE_DATE(i.year::INT, i.month::INT, 1) + INTERVAL 1 MONTH)
        ) AS days_in_month
    FROM inventory i JOIN products p ON i.product_id = p.product_id
    WHERE i.stockout_days > 0
),
demand AS (
    SELECT *,
           GREATEST(days_in_month - stockout_days, 1)                AS selling_days,
           units_sold * 1.0 / GREATEST(days_in_month - stockout_days, 1) AS avg_daily_demand
    FROM inv
)
SELECT
    category,
    SUM(avg_daily_demand * stockout_days * price)       AS phantom_corrected_1x,
    SUM(avg_daily_demand * 2 * stockout_days * price)   AS phantom_cap_2x,
    SUM(stockout_days)                                  AS total_stockout_days,
    COUNT(DISTINCT product_id)                          AS products_affected
FROM demand
GROUP BY category ORDER BY phantom_corrected_1x DESC;


-- 2. Monthly web_traffic sessions vs stockout_days (same month)
SELECT
    EXTRACT(year FROM wt.date)::INT AS year,
    EXTRACT(month FROM wt.date)::INT AS month,
    SUM(wt.sessions)                AS total_sessions,
    SUM(i.stockout_days)            AS total_stockout_days
FROM web_traffic wt
JOIN inventory i
    ON EXTRACT(year FROM wt.date)::INT  = i.year
    AND EXTRACT(month FROM wt.date)::INT = i.month
WHERE i.stockout_days > 0
GROUP BY EXTRACT(year FROM wt.date)::INT, EXTRACT(month FROM wt.date)::INT
ORDER BY year, month;


-- 3. Top 10 SKUs by corrected phantom revenue
WITH inv AS (
    SELECT i.product_id, i.units_sold, i.stockout_days, p.category, p.price,
           DATE_DIFF('day',
               MAKE_DATE(i.year::INT, i.month::INT, 1),
               (MAKE_DATE(i.year::INT, i.month::INT, 1) + INTERVAL 1 MONTH)
           ) AS days_in_month
    FROM inventory i JOIN products p ON i.product_id = p.product_id
    WHERE i.stockout_days > 0
),
demand AS (
    SELECT *,
           GREATEST(days_in_month - stockout_days, 1) AS selling_days,
           units_sold * 1.0 / GREATEST(days_in_month - stockout_days, 1) AS avg_daily_demand
    FROM inv
)
SELECT product_id, category, price,
       SUM(avg_daily_demand * stockout_days * price) AS phantom_1x,
       SUM(stockout_days) AS total_stockout_days
FROM demand
GROUP BY product_id, category, price
ORDER BY phantom_1x DESC LIMIT 10;
