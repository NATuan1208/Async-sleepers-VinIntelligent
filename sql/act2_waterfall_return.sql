-- Act 2: Total refund cost 10Y from returns table
SELECT SUM(refund_amount) AS return_cost_10y
FROM returns;
