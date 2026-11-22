-- Silver: Consolidation des mobilités douces, parkings et bornes de recharge
WITH unified_staging AS (
    SELECT * FROM {{ ref('stg_veloh_stations') }}
    UNION ALL
    SELECT * FROM {{ ref('stg_parkings_vdl') }}
    UNION ALL
    SELECT * FROM {{ ref('stg_chargy_stations') }}
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
)
SELECT
    u.facility_id,
    u.facility_type,
    u.facility_name,
    COALESCE(
        TRY_CAST(u.raw_observed_at AS TIMESTAMP),
        TRY_STRPTIME(
            REGEXP_EXTRACT(u.raw_observed_at, '([0-9]{1,2}\\s+[A-Za-z]{3}\\s+[0-9]{4}\\s+[0-9]{2}:[0-9]{2}:[0-9]{2})'),
            '%d %b %Y %H:%M:%S'
        ),
        CURRENT_TIMESTAMP
    ) AS observed_at_utc,
    u.available_capacity,
    u.total_capacity,
    u.opening_hours,
    CASE
        WHEN u.facility_type = 'PARKING' AND (u.facility_name LIKE '%Bouillon%' OR u.facility_name LIKE '%P+R%') THEN 0.00
        WHEN u.facility_type = 'PARKING' AND (u.facility_name LIKE '%Knuedler%' OR u.facility_name LIKE '%Monterey%') THEN 2.80
        WHEN u.facility_type = 'PARKING' AND (u.facility_name LIKE '%Théâtre%' OR u.facility_name LIKE '%Glacis%') THEN 2.00
        WHEN u.facility_type = 'PARKING' THEN 2.50
        WHEN u.facility_type = 'BIKE_SHARING' THEN 0.00
        ELSE NULL
    END AS hourly_rate_eur,
    CASE
        WHEN u.facility_type = 'PARKING' AND (u.facility_name LIKE '%Bouillon%' OR u.facility_name LIKE '%P+R%') THEN 'P+R gratuit 24h'
        WHEN u.facility_type = 'PARKING' AND (u.facility_name LIKE '%Knuedler%' OR u.facility_name LIKE '%Monterey%') THEN '2.80 €/h (1ère-2ème h), puis 3.20 €/h'
        WHEN u.facility_type = 'PARKING' AND u.facility_name LIKE '%Glacis%' THEN '1.00 €/h (8h-18h), gratuit nuit/WE'
        WHEN u.facility_type = 'PARKING' THEN '2.50 €/h tarif standard'
        WHEN u.facility_type = 'BIKE_SHARING' THEN 'Gratuit < 30min avec abonnement'
        WHEN u.facility_type = 'EV_CHARGING' THEN '0.35 €/kWh AC 22kW'
        ELSE 'Tarif non applicable'
    END AS tariff_details,
    (u.facility_type = 'PARKING' AND (u.facility_name LIKE '%Bouillon%' OR u.facility_name LIKE '%P+R%')) AS is_free_pr,
    CASE
        WHEN u.total_capacity > 0 THEN ROUND((u.total_capacity - u.available_capacity) * 100.0 / u.total_capacity, 1)
        ELSE NULL
    END AS occupancy_rate,
    COALESCE(u.lat, c.lat) AS lat,
    COALESCE(u.lon, c.lon) AS lon,
    COALESCE(c.code_lau, u.raw_commune_name) AS commune_lau,
    c.canton,
    u.source_id
FROM unified_staging u
LEFT JOIN ref_communes c
    ON LOWER(u.raw_commune_name) = LOWER(c.commune_name)
    OR LOWER(u.raw_commune_name) = LOWER(c.commune_name_lb)
    OR u.raw_commune_name = c.code_lau
