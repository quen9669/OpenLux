-- Staging: Extraction brute des prix immobiliers Observatoire depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_csv('data/bronze/housing_observatoire/**/*.csv.gz', header = true, union_by_name = true)
)
SELECT DISTINCT
    commune_name::VARCHAR AS raw_commune_name,
    property_type::VARCHAR AS property_type,
    reference_period::VARCHAR AS reference_period,
    price_eur_m2::DOUBLE AS price_eur_m2,
    transactions_count::INTEGER AS transactions_count,
    'housing_observatoire' AS source_id
FROM raw_source
