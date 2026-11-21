-- Gold: Data Mart final de l'immobilier et de la construction au Luxembourg
SELECT
    record_id,
    record_type,
    property_type,
    reference_period,
    observed_at_utc,
    price_eur_m2,
    units_count,
    lat,
    lon,
    commune_lau,
    canton,
    source_id
FROM {{ ref('silver_housing') }}
