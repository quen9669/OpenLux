-- Silver: Consolidation factuelle des annonces de marché, statistiques de prix et autorisations de bâtir
WITH obs_raw AS (
    SELECT *
    FROM {{ ref('stg_housing_observatoire') }}
    WHERE raw_commune_name != 'Moyenne nationale'
),
obs AS (
    SELECT
        raw_commune_name || '_' || property_type || '_' || reference_period AS record_id,
        'STATISTIC_OBSERVATOIRE' AS record_type,
        property_type,
        'EXISTING' AS market_segment,
        reference_period,
        NULL::DOUBLE AS price_eur,
        NULL::DOUBLE AS surface_m2,
        price_eur_m2,
        NULL::INTEGER AS bedrooms_count,
        NULL::INTEGER AS bathrooms_count,
        NULL::INTEGER AS rooms_count,
        false AS has_balcony,
        false AS has_terrace,
        false AS has_garden,
        false AS has_parking_or_garage,
        false AS has_elevator,
        NULL::INTEGER AS floor_number,
        NULL::INTEGER AS construction_year,
        NULL::VARCHAR AS energy_class,
        NULL::VARCHAR AS thermal_insulation_class,
        'Statistique de prix médian observatoire officiel'::VARCHAR AS description,
        NULL::VARCHAR AS street_name,
        NULL::VARCHAR AS postal_code,
        'Commune-Wide'::VARCHAR AS neighborhood_or_quartier,
        NULL::VARCHAR AS listing_url,
        transactions_count AS units_count,
        NULL::TIMESTAMP AS observed_at_utc,
        NULL::DOUBLE AS lat,
        NULL::DOUBLE AS lon,
        CASE
            WHEN raw_commune_name IN ('Bascharage', 'Clémency', 'Kaerjeng') THEN 'Käerjeng'
            WHEN raw_commune_name IN ('Boevange-sur-Attert', 'Tuntange') THEN 'Helperknapp'
            WHEN raw_commune_name IN ('Bous', 'Waldbredimus') THEN 'Bous-Waldbredimus'
            WHEN raw_commune_name IN ('Burmerange', 'Wellenstein') THEN 'Schengen'
            WHEN raw_commune_name IN ('Ermsdorf', 'Medernach') THEN 'Vallée de l''Ernz'
            WHEN raw_commune_name = 'Eschweiler' THEN 'Wiltz'
            WHEN raw_commune_name IN ('Grosbous', 'Wahl', 'Grosbus-Wal', 'Grosbous-Wal') THEN 'Groussbus-Wal'
            WHEN raw_commune_name IN ('Heiderscheid', 'Neunhausen') THEN 'Esch-sur-Sûre'
            WHEN raw_commune_name IN ('Heinerscheid', 'Munshausen') THEN 'Clervaux'
            WHEN raw_commune_name IN ('Hobscheid', 'Septfontaines') THEN 'Habscht'
            WHEN raw_commune_name IN ('Hoscheid', 'Hosingen') THEN 'Parc Hosingen'
            WHEN raw_commune_name IN ('Mompach', 'Rosport') THEN 'Rosport-Mompach'
            WHEN raw_commune_name = 'Petange' THEN 'Pétange'
            WHEN raw_commune_name = 'Erpeldange' THEN 'Erpeldange-sur-Sûre'
            WHEN raw_commune_name = 'Luxembourg-Ville' THEN 'Luxembourg'
            ELSE raw_commune_name
        END AS raw_commune_name,
        NULL::VARCHAR AS canton_override,
        source_id
    FROM obs_raw
),
statec AS (
    SELECT
        record_id,
        'STATISTIC_STATEC' AS record_type,
        property_type,
        'NEW_VEFA' AS market_segment,
        reference_period,
        NULL::DOUBLE AS price_eur,
        NULL::DOUBLE AS surface_m2,
        NULL::DOUBLE AS price_eur_m2,
        NULL::INTEGER AS bedrooms_count,
        NULL::INTEGER AS bathrooms_count,
        NULL::INTEGER AS rooms_count,
        false AS has_balcony,
        false AS has_terrace,
        false AS has_garden,
        false AS has_parking_or_garage,
        false AS has_elevator,
        NULL::INTEGER AS floor_number,
        NULL::INTEGER AS construction_year,
        NULL::VARCHAR AS energy_class,
        NULL::VARCHAR AS thermal_insulation_class,
        'Statistique des autorisations de bâtir délivrées (STATEC)'::VARCHAR AS description,
        NULL::VARCHAR AS street_name,
        NULL::VARCHAR AS postal_code,
        canton_name AS neighborhood_or_quartier,
        NULL::VARCHAR AS listing_url,
        units_authorized AS units_count,
        TRY_CAST(raw_observed_at AS TIMESTAMP) AS observed_at_utc,
        NULL::DOUBLE AS lat,
        NULL::DOUBLE AS lon,
        raw_commune_name,
        canton_name AS canton_override,
        source_id
    FROM {{ ref('stg_housing_statec') }}
),
market_listings AS (
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
unified AS (
    SELECT * FROM obs
    UNION ALL
    SELECT * FROM statec
    UNION ALL
    SELECT * FROM market_listings
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
    CASE
        WHEN LOWER(u.property_type) LIKE '%studio%' OR LOWER(u.description) LIKE '%studio%' OR u.property_type = 'Studio'
        THEN COALESCE(u.bedrooms_count, 0)
        ELSE u.bedrooms_count
    END AS bedrooms_count,
    u.bathrooms_count,
    CASE
        WHEN LOWER(u.property_type) LIKE '%studio%' OR LOWER(u.description) LIKE '%studio%' OR u.property_type = 'Studio'
        THEN COALESCE(u.rooms_count, 1)
        ELSE u.rooms_count
    END AS rooms_count,
    u.has_balcony,
    u.has_terrace,
    u.has_garden,
    u.has_parking_or_garage,
    u.has_elevator,
    u.floor_number,
    u.construction_year,
    u.energy_class,
    u.thermal_insulation_class,
    u.description,
    u.street_name,
    u.postal_code,
    u.neighborhood_or_quartier,
    COALESCE(c.code_lau, u.raw_commune_name) AS commune_lau,
    COALESCE(c.commune_name, u.raw_commune_name) AS commune_name,
    COALESCE(c.canton, u.canton_override, 'Luxembourg') AS canton,
    COALESCE(u.lat, c.lat) AS lat,
    COALESCE(u.lon, c.lon) AS lon,
    u.listing_url,
    u.units_count,
    u.source_id
FROM unified u
LEFT JOIN ref_communes c
    ON LOWER(u.raw_commune_name) = LOWER(c.commune_name)
    OR LOWER(u.raw_commune_name) = LOWER(c.commune_name_lb)
    OR u.raw_commune_name = c.code_lau
