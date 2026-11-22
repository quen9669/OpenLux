-- Silver: Nettoyage et typage strict des événements trafic autoroutiers CITA
WITH base AS (
    SELECT * FROM {{ ref('stg_traffic_cita') }}
)
SELECT
    event_id,
    road_name,
    situation_type,
    CASE
        WHEN raw_start_time IS NULL OR raw_start_time LIKE '2026-11-20%' OR TRY_CAST(raw_start_time AS TIMESTAMP) IS NULL
        THEN collected_at_utc
        ELSE TRY_CAST(raw_start_time AS TIMESTAMP)
    END AS observed_at_utc,
    lat,
    lon,
    NULL::VARCHAR AS commune_lau,
    traffic_comment,
    source_id
FROM base
WHERE event_id IS NOT NULL
