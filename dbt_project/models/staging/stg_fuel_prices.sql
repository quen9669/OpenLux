-- Staging: Extraction brute des prix maxima des carburants depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/fuel_prices_lu/**/*.json.gz', union_by_name = true)
)
SELECT DISTINCT
    fuel_type::VARCHAR AS fuel_type,
    observed_at::VARCHAR AS raw_observed_at,
    price_eur_per_litre::DOUBLE AS price_eur_per_litre,
    price_change_eur::DOUBLE AS price_change_eur,
    'fuel_prices_lu' AS source_id
FROM raw_source
