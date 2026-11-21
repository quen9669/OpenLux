-- Silver: Consolidation des mouvements aériens et de l'exposition au bruit
WITH unified_staging AS (
    SELECT * FROM {{ ref('stg_aviation_opensky_lu') }}
    UNION ALL
    SELECT * FROM {{ ref('stg_noise_zones_lu') }}
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
)
SELECT
    u.record_id,
    u.record_type,
    u.callsign_or_zone,
    TRY_CAST(u.raw_observed_at AS TIMESTAMP) AS observed_at_utc,
    u.altitude_m_or_dba,
    u.status,
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
