-- Silver: Typage strict et normalisation temporelle des prix maxima des carburants
SELECT
    fuel_type,
    TRY_CAST(raw_observed_at AS TIMESTAMP) AS observed_at_utc,
    price_eur_per_litre,
    price_change_eur,
    source_id
FROM {{ ref('stg_fuel_prices') }}
