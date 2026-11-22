-- Staging: Extraction brute des prix spot électricité DE-LU depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/electricity_spot_delu/**/*.json.gz', union_by_name = true)
)
SELECT DISTINCT
    observed_at::VARCHAR AS raw_observed_at,
    price_eur_per_mwh::DOUBLE AS price_eur_per_mwh,
    bidding_zone::VARCHAR AS bidding_zone,
    'electricity_spot_delu' AS source_id
FROM raw_source
WHERE observed_at IS NOT NULL
