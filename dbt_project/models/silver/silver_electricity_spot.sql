-- Silver: Typage strict et normalisation horaire des prix spot électricité Day-Ahead DE-LU
SELECT
    TRY_CAST(raw_observed_at AS TIMESTAMP) AS observed_at_utc,
    price_eur_per_mwh,
    bidding_zone,
    source_id
FROM {{ ref('stg_electricity_spot') }}
