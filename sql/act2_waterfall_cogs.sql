-- Act 2: Total COGS 10Y from sales table (source of truth per audit)
-- sales.COGS is the daily aggregate — consistent with sales.Revenue spine
SELECT SUM(COGS) AS true_cogs_10y
FROM sales;
