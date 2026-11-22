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
    CASE
        WHEN TRY_CAST(u.raw_start_date AS BIGINT) IS NOT NULL THEN to_timestamp(TRY_CAST(u.raw_start_date AS BIGINT) / 1000.0)
        ELSE TRY_CAST(u.raw_start_date AS TIMESTAMP)
    END AS start_date,
    CASE
        WHEN TRY_CAST(u.raw_end_date AS BIGINT) IS NOT NULL THEN to_timestamp(TRY_CAST(u.raw_end_date AS BIGINT) / 1000.0)
        ELSE TRY_CAST(u.raw_end_date AS TIMESTAMP)
    END AS end_date,
    u.impact_level,
    u.title,
    CASE
        WHEN TRY_CAST(u.raw_observed_at AS BIGINT) IS NOT NULL THEN to_timestamp(TRY_CAST(u.raw_observed_at AS BIGINT) / 1000.0)
        ELSE TRY_CAST(u.raw_observed_at AS TIMESTAMP)
    END AS observed_at_utc,
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
