-- Silver: Consolidation de la vie citoyenne (pétitions CHD et statistiques emploi ADEM)
WITH petitions AS (
    SELECT
        petition_id AS record_id,
        'PETITION' AS record_type,
        title AS title_or_indicator,
        signatures_count,
        NULL::DOUBLE AS rate_value,
        status,
        TRY_CAST(raw_deposited_at AS TIMESTAMP) AS observed_at_utc,
        'Luxembourg' AS raw_commune_name,
        source_id
    FROM {{ ref('stg_petitions_chd') }}
),
adem AS (
    SELECT
        reference_month || '_' || raw_commune_name AS record_id,
        'UNEMPLOYMENT' AS record_type,
        'DEMANDEURS_EMPLOI' AS title_or_indicator,
        jobseekers_count AS signatures_count,
        unemployment_rate_pct AS rate_value,
        reference_month AS status,
        COALESCE(TRY_CAST(reference_month || '-01 00:00:00' AS TIMESTAMP), '2026-01-01 00:00:00'::TIMESTAMP) AS observed_at_utc,
        raw_commune_name,
        source_id
    FROM {{ ref('stg_unemployment_adem') }}
),
unified AS (
    SELECT * FROM petitions
    UNION ALL
    SELECT * FROM adem
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
)
SELECT
    u.record_id,
    u.record_type,
    u.title_or_indicator,
    u.signatures_count,
    u.rate_value,
    u.status,
    u.observed_at_utc,
    c.lat,
    c.lon,
    COALESCE(c.code_lau, u.raw_commune_name) AS commune_lau,
    c.canton,
    u.source_id
FROM unified u
LEFT JOIN ref_communes c
    ON LOWER(u.raw_commune_name) = LOWER(c.commune_name)
    OR LOWER(u.raw_commune_name) = LOWER(c.commune_name_lb)
    OR u.raw_commune_name = c.code_lau
