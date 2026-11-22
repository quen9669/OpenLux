-- Silver: Nettoyage et enrichissement des parkings publics et P+R
WITH raw_parkings AS (
    SELECT * FROM {{ ref('stg_parkings_vdl') }}
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
)
SELECT
    p.parking_id,
    p.parking_name,
    COALESCE(
        TRY_CAST(p.raw_observed_at AS TIMESTAMP),
        TRY_STRPTIME(
            REGEXP_EXTRACT(p.raw_observed_at, '([0-9]{1,2} [A-Za-z]{3} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2})'),
            '%d %b %Y %H:%M:%S'
        ),
        CURRENT_TIMESTAMP
    ) AS observed_at_utc,
    p.available_spaces,
    p.total_capacity,
    CASE
        WHEN p.total_capacity >= p.available_spaces THEN p.total_capacity - p.available_spaces
        ELSE 0
    END AS occupied_spaces,
    CASE
        WHEN p.total_capacity > 0 THEN ROUND((p.total_capacity - p.available_spaces) * 100.0 / p.total_capacity, 1)
        ELSE NULL
    END AS occupancy_rate,
    p.trend,
    p.is_open,
    (p.is_full OR (p.total_capacity > 0 AND p.available_spaces = 0)) AS is_full,
    p.is_out_of_order,
    p.is_free_pr,
    p.opening_hours,
    CASE
        WHEN p.is_free_pr THEN 0.00
        WHEN p.parking_name LIKE '%Knuedler%' OR p.parking_name LIKE '%Monterey%' THEN 2.80
        WHEN p.parking_name LIKE '%Théâtre%' OR p.parking_name LIKE '%Glacis%' THEN 2.00
        ELSE 2.50
    END AS hourly_rate_eur,
    CASE
        WHEN p.is_free_pr THEN 'P+R gratuit 24h avec navette'
        WHEN p.parking_name LIKE '%Knuedler%' OR p.parking_name LIKE '%Monterey%' THEN '2.80 €/h (1ère-2ème h), puis 3.20 €/h'
        WHEN p.parking_name LIKE '%Glacis%' THEN '1.00 €/h (8h-18h), gratuit nuit/WE'
        ELSE '2.50 €/h tarif standard'
    END AS tariff_details,
    COALESCE(p.lat, c.lat) AS lat,
    COALESCE(p.lon, c.lon) AS lon,
    COALESCE(c.code_lau, p.raw_commune_name) AS commune_lau,
    c.canton,
    p.source_id
FROM raw_parkings p
LEFT JOIN ref_communes c
    ON LOWER(p.raw_commune_name) = LOWER(c.commune_name)
    OR LOWER(p.raw_commune_name) = LOWER(c.commune_name_lb)
    OR p.raw_commune_name = c.code_lau
