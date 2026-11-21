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
    TRY_CAST(u.raw_observed_at AS TIMESTAMP) AS observed_at_utc,
    u.available_capacity,
    u.total_capacity,
    u.opening_hours,
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
