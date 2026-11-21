-- Silver: Consolidation et enrichissement géographique des chantiers autoroutiers et communaux
WITH unified_staging AS (
    SELECT * FROM {{ ref('stg_roadworks_cita') }}
    UNION ALL
    SELECT * FROM {{ ref('stg_roadworks_vdl') }}
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
)
SELECT
    u.work_id,
    u.authority,
    u.road_name,
    TRY_CAST(u.raw_start_date AS TIMESTAMP) AS start_date,
    TRY_CAST(u.raw_end_date AS TIMESTAMP) AS end_date,
    u.impact_level,
    u.title,
    TRY_CAST(u.raw_observed_at AS TIMESTAMP) AS observed_at_utc,
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
