-- Silver: Consolidation des prix immobiliers et des permis de construire
WITH obs AS (
    SELECT
        raw_commune_name || '_' || property_type || '_' || reference_period AS record_id,
        'SALE_PRICE' AS record_type,
        property_type,
        reference_period,
        price_eur_m2,
        transactions_count AS units_count,
        NULL::TIMESTAMP AS observed_at_utc,
        NULL::DOUBLE AS lat,
        NULL::DOUBLE AS lon,
        raw_commune_name,
        source_id
    FROM {{ ref('stg_housing_observatoire') }}
),
statec AS (
    SELECT
        record_id,
        'BUILDING_PERMIT' AS record_type,
        property_type,
        reference_period,
        NULL::DOUBLE AS price_eur_m2,
        units_authorized AS units_count,
        TRY_CAST(raw_observed_at AS TIMESTAMP) AS observed_at_utc,
        lat,
        lon,
        raw_commune_name,
        source_id
    FROM {{ ref('stg_housing_statec') }}
),
unified AS (
    SELECT * FROM obs
    UNION ALL
    SELECT * FROM statec
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
)
SELECT
    u.record_id,
    u.record_type,
    u.property_type,
    u.reference_period,
    COALESCE(u.observed_at_utc, CURRENT_TIMESTAMP) AS observed_at_utc,
    u.price_eur_m2,
    u.units_count,
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
