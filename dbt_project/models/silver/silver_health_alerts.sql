-- Silver: Consolidation des alertes sanitaires, concentrations polliniques et défibrillateurs
WITH pollen AS (
    SELECT
        specie AS record_id,
        'POLLEN' AS record_type,
        specie AS headline_or_name,
        risk_level AS status_or_severity,
        grains_m3::DOUBLE AS metric_value,
        TRY_CAST(raw_observed_at AS TIMESTAMP) AS observed_at_utc,
        NULL::DOUBLE AS lat,
        NULL::DOUBLE AS lon,
        raw_commune_name,
        source_id
    FROM {{ ref('stg_pollen_lu') }}
),
aed AS (
    SELECT
        aed_id AS record_id,
        'AED' AS record_type,
        location_name AS headline_or_name,
        access_hours AS status_or_severity,
        NULL::DOUBLE AS metric_value,
        CURRENT_TIMESTAMP AS observed_at_utc,
        lat,
        lon,
        raw_commune_name,
        source_id
    FROM {{ ref('stg_aed_defib_lu') }}
),
alert AS (
    SELECT
        alert_id AS record_id,
        'LU_ALERT' AS record_type,
        headline AS headline_or_name,
        severity AS status_or_severity,
        NULL::DOUBLE AS metric_value,
        TRY_CAST(raw_effective_utc AS TIMESTAMP) AS observed_at_utc,
        NULL::DOUBLE AS lat,
        NULL::DOUBLE AS lon,
        raw_commune_name,
        source_id
    FROM {{ ref('stg_lu_alert') }}
),
unified AS (
    SELECT * FROM pollen
    UNION ALL
    SELECT * FROM aed
    UNION ALL
    SELECT * FROM alert
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
)
SELECT
    u.record_id,
    u.record_type,
    u.headline_or_name,
    u.status_or_severity,
    u.metric_value,
    u.observed_at_utc,
    COALESCE(u.lat, c.lat) AS lat,
    COALESCE(u.lon, c.lon) AS lon,
    COALESCE(c.code_lau, u.raw_commune_name) AS commune_lau,
    c.canton,
    u.source_id
FROM unified u
LEFT JOIN ref_communes c
    ON LOWER(u.raw_commune_name) = LOWER(c.commune_name)
    OR LOWER(u.raw_commune_name) = LOWER(c.commune_name_lb)
    OR u.raw_commune_name = c.code_lau
