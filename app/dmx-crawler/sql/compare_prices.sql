-- Current price comparison for one or all products.
-- Add `AND p.id = '<product uuid>'` to current_price for a single product.
WITH current_product AS (
    SELECT p.id AS product_id, pcv.name
    FROM products p
    JOIN product_content_versions pcv ON pcv.product_id = p.id
    WHERE pcv.valid_to IS NULL
),
current_price AS (
    SELECT plv.product_id, l.code, plv.sale_price, plv.stock_status,
           plv.delivery_json, plv.valid_from
    FROM product_location_versions plv
    JOIN locations l ON l.id = plv.location_id
    WHERE plv.valid_to IS NULL
      AND l.code IN ('hcm', 'hanoi', 'danang')
)
SELECT
    cp.product_id,
    cp.name,
    MAX(cpr.sale_price) FILTER (WHERE cpr.code = 'hcm') AS price_hcm,
    MAX(cpr.sale_price) FILTER (WHERE cpr.code = 'hanoi') AS price_hanoi,
    MAX(cpr.sale_price) FILTER (WHERE cpr.code = 'danang') AS price_danang,
    MAX(cpr.stock_status) FILTER (WHERE cpr.code = 'hcm') AS stock_hcm,
    MAX(cpr.stock_status) FILTER (WHERE cpr.code = 'hanoi') AS stock_hanoi,
    MAX(cpr.stock_status) FILTER (WHERE cpr.code = 'danang') AS stock_danang
FROM current_product cp
JOIN current_price cpr ON cpr.product_id = cp.product_id
GROUP BY cp.product_id, cp.name
ORDER BY cp.name;
