-- Act 2: Phantom revenue from stockouts (ESTIMATED — document assumptions clearly)
--
-- Methodology assumptions (must be shown in notebook markdown cell):
--   1. avg_daily_demand = units_sold / selling_days
--      where selling_days = MAX(days_in_month - stockout_days, 1)
--   2. lost_units = avg_daily_demand * stockout_days
--   3. lost_revenue = lost_units * product.price
--   4. Demand capped at 2x observed to prevent extrapolation explosion
--   5. Only rows with stockout_days > 0 included
--
-- This number is LABELED "Phantom (estimated)" on charts — not an actual cash loss

WITH inv AS (
    SELECT
        i.year,
        i.month,
        i.product_id,
        i.units_sold,
        i.stockout_days,
        DATE_DIFF('day',
            MAKE_DATE(i.year::INT, i.month::INT, 1),
            (MAKE_DATE(i.year::INT, i.month::INT, 1) + INTERVAL 1 MONTH)
        )                   AS days_in_month,
        p.price
    FROM inventory i
    JOIN products p ON i.product_id = p.product_id
    WHERE i.stockout_days > 0
),
demand AS (
    SELECT *,
        GREATEST(days_in_month - stockout_days, 1)           AS selling_days,
        i.units_sold / GREATEST(days_in_month - stockout_days, 1) AS avg_daily_demand
    FROM inv i
)
SELECT
    year,
    SUM(
        -- cap demand at 2x observed
        LEAST(avg_daily_demand * 2, avg_daily_demand * 2)
        * stockout_days
        * price
    ) AS phantom_revenue
FROM demand
GROUP BY year
ORDER BY year;
