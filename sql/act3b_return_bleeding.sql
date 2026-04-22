-- Act 3B: The Return Bleeding
-- MCQ rule: return rate = COUNT(returns) / COUNT(order_items) by RECORD, not quantity

-- 1. Return rate by size × category heatmap
WITH order_lines AS (
    SELECT DISTINCT oi.order_id, p.category, p.size
    FROM order_items oi JOIN products p ON oi.product_id = p.product_id
)
SELECT
    ol.size,
    ol.category,
    COUNT(DISTINCT ol.order_id)                                         AS total_orders,
    COUNT(DISTINCT r.order_id)                                          AS returned_orders,
    COUNT(DISTINCT r.order_id) * 1.0 / COUNT(DISTINCT ol.order_id)     AS return_rate,
    SUM(r.refund_amount)                                                AS total_refund
FROM order_lines ol
LEFT JOIN returns r ON ol.order_id = r.order_id
GROUP BY ol.size, ol.category
ORDER BY return_rate DESC;


-- 2. Reviews as return predictor — rating → P(return) by rating bucket
SELECT
    rv.rating,
    COUNT(DISTINCT rv.order_id)                                             AS n_reviews,
    COUNT(DISTINCT r.order_id)                                              AS n_returned,
    COUNT(DISTINCT r.order_id) * 1.0 / COUNT(DISTINCT rv.order_id)         AS return_rate
FROM reviews rv
LEFT JOIN returns r ON rv.order_id = r.order_id
GROUP BY rv.rating ORDER BY rv.rating;


-- 3. Top 10 worst return-cost categories (absolute refund VND)
WITH order_lines AS (
    SELECT DISTINCT oi.order_id, p.category
    FROM order_items oi JOIN products p ON oi.product_id = p.product_id
)
SELECT ol.category,
       COUNT(DISTINCT ol.order_id)  AS total_orders,
       COUNT(DISTINCT r.order_id)   AS returned_orders,
       COUNT(DISTINCT r.order_id) * 1.0 / COUNT(DISTINCT ol.order_id) AS return_rate,
       SUM(r.refund_amount)         AS total_refund
FROM order_lines ol
LEFT JOIN returns r ON ol.order_id = r.order_id
GROUP BY ol.category
ORDER BY total_refund DESC;
