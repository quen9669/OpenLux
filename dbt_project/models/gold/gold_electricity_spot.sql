-- Gold: Data Mart final des prix spot électricité Day-Ahead zone DE-LU
SELECT
    observed_at_utc,
    price_eur_per_mwh,
    bidding_zone,
    data_origin,
    is_imputed,
    source_id
FROM {{ ref('silver_electricity_spot') }}
