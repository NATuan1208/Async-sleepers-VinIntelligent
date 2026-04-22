-- Act 2: Total discount cost 10Y
-- MCQ rule: promo applied = promo_id IS NOT NULL OR promo_id_2 IS NOT NULL
-- Deduplicate the 16 known duplicate order_items natural keys via ROW_NUMBER
WITH deduped AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY order_id, product_id, promo_id, promo_id_2
               ORDER BY discount_amount DESC
           ) AS rn
    FROM order_items
)
SELECT SUM(d.discount_amount) AS discount_cost_10y
FROM deduped d
WHERE d.rn = 1;
