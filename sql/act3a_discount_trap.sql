-- Act 3A: The Discount Trap
-- MCQ definition: discount order = promo_id IS NOT NULL OR promo_id_2 IS NOT NULL

-- 1. Discount rate by promo_type × category (heatmap matrix)
WITH promo_revenue AS (
    SELECT
        COALESCE(pr.promo_type, 'unknown') AS promo_type,
        p.category,
        SUM(oi.quantity * oi.unit_price)   AS gross_revenue,
        SUM(oi.discount_amount)            AS discount_cost
    FROM order_items oi
    JOIN orders o     ON oi.order_id   = o.order_id
    JOIN products p   ON oi.product_id = p.product_id
    LEFT JOIN promotions pr
        ON oi.promo_id = pr.promo_id OR oi.promo_id_2 = pr.promo_id
    WHERE (oi.promo_id IS NOT NULL OR oi.promo_id_2 IS NOT NULL)
      AND o.order_status NOT IN ('cancelled', 'returned')
    GROUP BY pr.promo_type, p.category
)
SELECT *, discount_cost / NULLIF(gross_revenue, 0) AS discount_rate
FROM promo_revenue ORDER BY discount_rate DESC;


-- 2. first_order_value quintile stratification (Anti-Pattern #4 — kill selection bias)
WITH customer_fov AS (
    SELECT o.customer_id,
           NTILE(5) OVER (ORDER BY MIN(oi.unit_price * oi.quantity)) AS fov_quintile
    FROM order_items oi JOIN orders o USING (order_id)
    GROUP BY o.customer_id
),
promo_by_quintile AS (
    SELECT
        cf.fov_quintile,
        COUNT(DISTINCT o.order_id)           AS n_orders,
        SUM(oi.discount_amount)              AS total_discount,
        SUM(oi.quantity * oi.unit_price)     AS total_revenue
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN customer_fov cf ON o.customer_id = cf.customer_id
    WHERE oi.promo_id IS NOT NULL OR oi.promo_id_2 IS NOT NULL
    GROUP BY cf.fov_quintile
)
SELECT *, total_discount / NULLIF(total_revenue, 0) AS discount_rate
FROM promo_by_quintile ORDER BY fov_quintile;


-- 3. Seasonal discount pattern (month of year)
SELECT EXTRACT(month FROM o.order_date)::INT AS month,
       SUM(oi.discount_amount)                 AS total_discount,
       SUM(oi.quantity * oi.unit_price)         AS total_revenue,
       SUM(oi.discount_amount) / SUM(oi.quantity * oi.unit_price) AS discount_rate
FROM order_items oi JOIN orders o ON oi.order_id = o.order_id
WHERE oi.promo_id IS NOT NULL OR oi.promo_id_2 IS NOT NULL
GROUP BY month ORDER BY month;
