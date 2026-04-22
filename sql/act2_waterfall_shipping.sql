-- Act 2: Shipping fees absorbed on cancelled orders
SELECT SUM(s.shipping_fee) AS shipping_absorbed_10y
FROM orders o
JOIN shipments s ON o.order_id = s.order_id
WHERE o.order_status = 'cancelled';
