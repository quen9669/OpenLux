-- Gold: Data Mart des statistiques officielles du logement (Observatoire de l'Habitat & STATEC)
SELECT
    record_id,
    record_type,
    property_type,
    market_segment,
    reference_period,
    price_eur_m2,
    units_count,
    permits_count,
    description,
    commune_lau,
    commune_name,
    canton,
    lat,
    lon,
    observed_at_utc,
    source_id
FROM {{ ref('silver_housing_stats') }}
