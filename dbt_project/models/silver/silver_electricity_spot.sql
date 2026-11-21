-- Silver: Typage strict et normalisation horaire des prix spot électricité Day-Ahead DE-LU
SELECT
    TRY_CAST(raw_observed_at AS TIMESTAMP) AS observed_at_utc,
    COALESCE(
        price_eur_per_mwh,
        LAG(price_eur_per_mwh) OVER (ORDER BY TRY_CAST(raw_observed_at AS TIMESTAMP)),
        LEAD(price_eur_per_mwh) OVER (ORDER BY TRY_CAST(raw_observed_at AS TIMESTAMP))
    ) AS price_eur_per_mwh,
    COALESCE(bidding_zone, 'DE-LU') AS bidding_zone,
    source_id
FROM {{ ref('stg_electricity_spot') }}
WHERE raw_observed_at IS NOT NULL
