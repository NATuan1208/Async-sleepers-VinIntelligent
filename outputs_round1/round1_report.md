# Round 1 Data Audit and MCQ Report

## 1. Warehouse Ingestion
- Tables ingested: 14
- Total rows loaded: 2960736

| table_name | source_file | row_count | column_count |
| --- | --- | --- | --- |
| order_items | order_items.csv | 714669 | 7 |
| orders | orders.csv | 646945 | 8 |
| payments | payments.csv | 646945 | 4 |
| shipments | shipments.csv | 566067 | 4 |
| customers | customers.csv | 121930 | 7 |

## 2. Data Audit Summary
- promo_null_and_applied_ratio: {'total_rows': 714669, 'promo_id_null_rows': 438353, 'promo_id_2_null_rows': 714463, 'promo_applied_rows': 276316, 'promo_applied_ratio': 0.3866349316956521}
- duplicate_order_items_natural_key: {'duplicated_keys': 16}
- cancelled_returned_order_ratio: {'total_orders': 646945, 'failed_like_orders': 95604, 'failed_like_ratio': 0.14777763179250167}

## 3. MCQ Computed Results
| question_id | metric_name | metric_value | note |
| --- | --- | --- | --- |
| Q1 | median_inter_order_gap_days | 144.0 | LAG over order_date by customer_id |
| Q2 | highest_margin_segment | Standard | AVG((price-cogs)/price) by segment |
| Q3 | top_streetwear_return_reason | wrong_size | Mode return_reason after returns-products join |
| Q4 | lowest_bounce_source | email_campaign | Min average bounce_rate by traffic_source |
| Q5 | promo_item_ratio | 0.3866349316956521 | Promo applied if promo_id OR promo_id_2 is not null |
| Q6 | highest_avg_orders_age_group | 55+ | Join orders-customers and average orders by valid age_group |
| Q7 | highest_revenue_region | East | Exclude cancelled/returned/failed-like statuses before regional revenue sum |
| Q8 | cancelled_orders_mode_payment_method | credit_card | orders vs payments match 100%, mode computed from orders(cancelled) |
| Q8_check | orders_vs_payments_match_ratio | 1.0 | compared_rows=646945, mismatched_rows=0 |
| Q9 | highest_return_rate_size_by_record_count | S | Return rate defined by record counts, not quantity |
| Q10 | installments_with_highest_avg_payment | 6 | Max average payment_value by installments |

## 4. MCQ Choice Mapping
| question_id | metric_value | selected_choice | choice_reason |
| --- | --- | --- | --- |
| Q1 | 144.0 | C | nearest_number distance=36.000000 |
| Q2 | Standard | D | exact_text matched |
| Q3 | wrong_size | B | exact_text matched |
| Q4 | email_campaign | C | exact_text matched |
| Q5 | 0.3866349316956521 | C | nearest_number distance=0.003365 |
| Q6 | 55+ | A | exact_text matched |
| Q7 | East | C | exact_text matched |
| Q8 | credit_card | A | exact_text matched |
| Q8_check | 1.0 | UNMAPPED | Question is not in choice key |
| Q9 | S | A | exact_text matched |
| Q10 | 6 | C | nearest_number distance=0.000000 |

## 5. Notes
- Q5 uses promo_id OR promo_id_2 to determine whether a line item has promotion.
- Q7 excludes cancelled/returned/failed-like order statuses when computing regional revenue.
- Q8 checks payment_method consistency between orders and payments before mode selection.
- Q9 return rate is calculated by record count, not quantity.
