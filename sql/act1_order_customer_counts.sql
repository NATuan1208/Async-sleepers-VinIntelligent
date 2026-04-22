-- Act 1: Annual order count and unique customers
SELECT
    EXTRACT(year FROM order_date)::INT AS year,
    COUNT(*)                            AS total_orders,
    COUNT(DISTINCT customer_id)         AS unique_customers
FROM orders
GROUP BY year
ORDER BY year;
