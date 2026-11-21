-- Silver: Consolidation des prix immobiliers, permis de construire et annonces de marché
WITH obs AS (
    SELECT
        raw_commune_name || '_' || property_type || '_' || reference_period AS record_id,
        'OBSERVATOIRE_MEDIAN' AS record_type,
        property_type,
        'EXISTING' AS market_segment,
        reference_period,
        NULL::DOUBLE AS price_eur,
        NULL::DOUBLE AS surface_m2,
        price_eur_m2,
        price_eur_m2 AS quartier_avg_price_m2,
        50.0::DOUBLE AS deal_opportunity_score,
        false AS is_good_deal,
        NULL::INTEGER AS bedrooms_count,
        NULL::VARCHAR AS energy_class,
        NULL::VARCHAR AS listing_url,
        transactions_count AS units_count,
        NULL::TIMESTAMP AS observed_at_utc,
        NULL::DOUBLE AS lat,
        NULL::DOUBLE AS lon,
        raw_commune_name,
        'Commune-Wide' AS neighborhood_or_quartier,
        source_id
    FROM {{ ref('stg_housing_observatoire') }}
),
statec AS (
    SELECT
        record_id,
        'BUILDING_PERMIT' AS record_type,
        property_type,
        'NEW_VEFA' AS market_segment,
        reference_period,
        NULL::DOUBLE AS price_eur,
        NULL::DOUBLE AS surface_m2,
        NULL::DOUBLE AS price_eur_m2,
        NULL::DOUBLE AS quartier_avg_price_m2,
        NULL::DOUBLE AS deal_opportunity_score,
        false AS is_good_deal,
        NULL::INTEGER AS bedrooms_count,
        NULL::VARCHAR AS energy_class,
        NULL::VARCHAR AS listing_url,
        units_authorized AS units_count,
        TRY_CAST(raw_observed_at AS TIMESTAMP) AS observed_at_utc,
        lat,
        lon,
        raw_commune_name,
        'Commune-Wide' AS neighborhood_or_quartier,
        source_id
    FROM {{ ref('stg_housing_statec') }}
),
market_deals AS (
    SELECT
        record_id,
        'MARKET_LISTING' AS record_type,
        property_type,
        market_segment,
        '2026-Q4' AS reference_period,
        price_eur,
        surface_m2,
        price_eur_m2,
        quartier_avg_price_m2,
        deal_opportunity_score,
        is_good_deal,
        bedrooms_count,
        energy_class,
        listing_url,
        1 AS units_count,
        CURRENT_TIMESTAMP AS observed_at_utc,
        NULL::DOUBLE AS lat,
        NULL::DOUBLE AS lon,
        commune_name AS raw_commune_name,
        neighborhood_or_quartier,
        source_id
    FROM {{ ref('ref_housing_market_deals') }}
),
unified AS (
    SELECT * FROM obs
    UNION ALL
    SELECT * FROM statec
    UNION ALL
    SELECT * FROM market_deals
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
)
SELECT
    u.record_id,
    u.record_type,
    u.property_type,
    u.market_segment,
    u.reference_period,
    COALESCE(u.observed_at_utc, CURRENT_TIMESTAMP) AS observed_at_utc,
    u.price_eur,
    u.surface_m2,
    u.price_eur_m2,
    u.quartier_avg_price_m2,
    u.deal_opportunity_score,
    u.is_good_deal,
    u.bedrooms_count,
    u.energy_class,
    u.listing_url,
    u.units_count,
    u.neighborhood_or_quartier,
    COALESCE(c.code_lau, u.raw_commune_name) AS commune_lau,
    COALESCE(c.commune_name, u.raw_commune_name) AS commune_name,
    c.canton,
    COALESCE(u.lat, c.lat) AS lat,
    COALESCE(u.lon, c.lon) AS lon,
    u.source_id
FROM unified u
LEFT JOIN ref_communes c
    ON LOWER(u.raw_commune_name) = LOWER(c.commune_name)
    OR LOWER(u.raw_commune_name) = LOWER(c.commune_name_lb)
    OR u.raw_commune_name = c.code_lau
