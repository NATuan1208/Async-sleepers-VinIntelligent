-- Act 1: Median order value (item total per order)
SELECT MEDIAN(item_total) AS aov_median
FROM (
    SELECT
        o.order_id,
        SUM(oi.quantity * oi.unit_price) AS item_total
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY o.order_id
);
