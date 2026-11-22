-- Silver: Nettoyage et typage strict des événements trafic autoroutiers CITA
WITH base AS (
    SELECT * FROM {{ ref('stg_traffic_cita') }}
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
),
default_lux AS (
    SELECT * FROM ref_communes WHERE code_lau = 'LU0704'
)
SELECT
    b.event_id,
    b.road_name,
    b.situation_type,
    CASE
        WHEN b.raw_start_time IS NULL OR TRY_CAST(b.raw_start_time AS TIMESTAMP) IS NULL
        THEN b.collected_at_utc
        ELSE TRY_CAST(b.raw_start_time AS TIMESTAMP)
    END AS observed_at_utc,
    COALESCE(b.lat, c.lat, d.lat) AS lat,
    COALESCE(b.lon, c.lon, d.lon) AS lon,
    COALESCE(c.code_lau, d.code_lau) AS commune_lau,
    COALESCE(c.canton, d.canton) AS canton,
    b.traffic_comment,
    b.source_id
FROM base b
CROSS JOIN default_lux d
LEFT JOIN ref_communes c
    ON LOWER(b.raw_commune_name) = LOWER(c.commune_name)
    OR LOWER(b.raw_commune_name) = LOWER(c.commune_name_lb)
    OR b.raw_commune_name = c.code_lau
WHERE b.event_id IS NOT NULL
