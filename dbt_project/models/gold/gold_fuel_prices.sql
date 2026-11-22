-- Gold: Data Mart final des prix maxima officiels des carburants au Luxembourg
SELECT
    fuel_type,
    observed_at_utc,
    price_eur_per_litre,
    price_change_eur,
    source_id
FROM {{ ref('silver_fuel_prices') }}
ORDER BY observed_at_utc DESC NULLS LAST, fuel_type
