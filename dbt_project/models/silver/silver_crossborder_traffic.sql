-- Silver: Consolidation, typage et enrichissement du trafic frontalier multimodal
WITH unified_staging AS (
    SELECT * FROM {{ ref('stg_traffic_fr_bisonfute') }}
    UNION ALL
    SELECT * FROM {{ ref('stg_traffic_de_autobahn') }}
    UNION ALL
    SELECT * FROM {{ ref('stg_traffic_be_trafiroutes') }}
    UNION ALL
    SELECT * FROM {{ ref('stg_rail_crossborder') }}
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
)
SELECT
    u.event_id,
    u.corridor,
    u.transport_mode,
    TRY_CAST(u.raw_observed_at AS TIMESTAMP) AS observed_at_utc,
    u.delay_minutes,
    u.status,
    u.comment,
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
