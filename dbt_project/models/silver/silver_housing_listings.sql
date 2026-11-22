-- Silver: Annonces immobilieres du marche (offres a la vente et location, 29 attributs factuels)
WITH market_listings AS (
    SELECT
        record_id,
        'LISTING' AS record_type,
        property_type,
        market_segment,
        '2026-Q4' AS reference_period,
        price_eur,
        surface_m2,
        price_eur_m2,
        bedrooms_count,
        bathrooms_count,
        rooms_count,
        has_balcony,
        has_terrace,
        has_garden,
        has_parking_or_garage,
        has_elevator,
        floor_number,
        construction_year,
        energy_class,
        thermal_insulation_class,
        description,
        street_name,
        postal_code,
        neighborhood_or_quartier,
        listing_url,
        1 AS units_count,
        CURRENT_TIMESTAMP AS observed_at_utc,
        lat,
        lon,
        commune_name AS raw_commune_name,
        canton AS canton_override,
        source_id
    FROM {{ ref('ref_housing_market_deals') }}
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }}
)
SELECT
    m.record_id,
    m.record_type,
    m.property_type,
    m.market_segment,
    m.price_eur,
    m.surface_m2,
    m.price_eur_m2,
    CASE
        WHEN LOWER(m.property_type) LIKE '%studio%' OR LOWER(m.description) LIKE '%studio%' OR m.property_type = 'Studio'
        THEN COALESCE(m.bedrooms_count, 0)
        ELSE m.bedrooms_count
    END AS bedrooms_count,
    m.bathrooms_count,
    CASE
        WHEN LOWER(m.property_type) LIKE '%studio%' OR LOWER(m.description) LIKE '%studio%' OR m.property_type = 'Studio'
        THEN COALESCE(m.rooms_count, 1)
        ELSE m.rooms_count
    END AS rooms_count,
    m.has_balcony,
    m.has_terrace,
    m.has_garden,
    m.has_parking_or_garage,
    m.has_elevator,
    m.floor_number,
    m.construction_year,
    m.energy_class,
    m.thermal_insulation_class,
    m.description,
    m.street_name,
    m.postal_code,
    m.neighborhood_or_quartier,
    COALESCE(c.code_lau, m.raw_commune_name) AS commune_lau,
    COALESCE(c.commune_name, m.raw_commune_name) AS commune_name,
    COALESCE(c.canton, m.canton_override, 'Luxembourg') AS canton,
    COALESCE(m.lat, c.lat) AS lat,
    COALESCE(m.lon, c.lon) AS lon,
    m.listing_url,
    m.units_count,
    m.observed_at_utc,
    m.source_id
FROM market_listings m
LEFT JOIN ref_communes c
    ON LOWER(m.raw_commune_name) = LOWER(c.commune_name)
    OR LOWER(m.raw_commune_name) = LOWER(c.commune_name_lb)
    OR m.raw_commune_name = c.code_lau
