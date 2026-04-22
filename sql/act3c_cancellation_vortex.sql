-- Act 3C: The Cancellation Vortex
-- MCQ Q8: credit_card leads cancelled orders
-- Cross-check: orders JOIN payments (100% match confirmed from Phase 1)

-- 1. Cancellation rate by payment method
SELECT
    py.payment_method,
    COUNT(DISTINCT o.order_id)                                                           AS total_orders,
    SUM(CASE WHEN o.order_status = 'cancelled' THEN 1 ELSE 0 END)                       AS cancelled_orders,
    SUM(CASE WHEN o.order_status = 'cancelled' THEN 1 ELSE 0 END) * 1.0
        / COUNT(DISTINCT o.order_id)                                                     AS cancel_rate
FROM orders o
JOIN payments py ON o.order_id = py.order_id
GROUP BY py.payment_method
ORDER BY cancel_rate DESC;


-- 2. CC cancelled orders: installments distribution (fraud vs auth-fail vs remorse)
SELECT
    py.installments,
    COUNT(*)                                         AS n_cancelled_cc_orders,
    AVG(py.payment_value)                            AS avg_payment_value
FROM orders o
JOIN payments py ON o.order_id = py.order_id
WHERE o.order_status = 'cancelled'
  AND py.payment_method = 'credit_card'
GROUP BY py.installments ORDER BY py.installments;


-- 3. Order value distribution: CC cancelled vs CC completed (percentiles)
SELECT
    CASE WHEN o.order_status = 'cancelled' THEN 'Cancelled' ELSE 'Completed' END AS status,
    COUNT(DISTINCT o.order_id) AS n_orders,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY py.payment_value) AS p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY py.payment_value) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY py.payment_value) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY py.payment_value) AS p95
FROM orders o
JOIN payments py ON o.order_id = py.order_id
WHERE py.payment_method = 'credit_card'
GROUP BY status;
