-- Silver: Consolidation des pistes cyclables, commerces ouverts et centres de recyclage
WITH unified_staging AS (
    SELECT * FROM {{ ref('stg_bike_lanes_lu') }}
    UNION ALL
    SELECT * FROM {{ ref('stg_open_sundays_vdl') }}
    UNION ALL
    SELECT * FROM {{ ref('stg_recycling_centers') }}
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
)
SELECT
    u.item_id,
    u.category,
    u.name,
    CASE
        WHEN u.raw_observed_at IS NULL OR TRY_CAST(u.raw_observed_at AS TIMESTAMP) IS NULL
        THEN u.collected_at_utc
        ELSE TRY_CAST(u.raw_observed_at AS TIMESTAMP)
    END AS observed_at_utc,
    u.status_or_schedule,
    u.details,
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
