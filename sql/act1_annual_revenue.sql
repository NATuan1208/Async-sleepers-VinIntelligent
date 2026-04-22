-- Act 1: Annual gross revenue and COGS from sales spine (2012-2022)
SELECT
    EXTRACT(year FROM Date)::INT AS year,
    SUM(Revenue)                  AS gross_revenue,
    SUM(COGS)                     AS total_cogs
FROM sales
GROUP BY year
ORDER BY year;
