-- Silver: Consolidation et enrichissement géographique des transports en commun
WITH unified_staging AS (
    SELECT * FROM {{ ref('stg_transit_mobiliteit') }}
    UNION ALL
    SELECT * FROM {{ ref('stg_transit_avl_rt') }}
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
)
SELECT
    u.line_id,
    u.network,
    TRY_CAST(u.raw_observed_at AS TIMESTAMP) AS observed_at_utc,
    u.delay_seconds,
    u.disruption_level,
    u.message,
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
