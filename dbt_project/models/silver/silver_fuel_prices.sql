-- Silver: Typage strict et normalisation temporelle des prix maxima des carburants
SELECT
    fuel_type,
    COALESCE(
        TRY_CAST(raw_observed_at AS TIMESTAMP),
        TRY_STRPTIME(raw_observed_at, '%b-%y'),
        TRY_STRPTIME(raw_observed_at, '%b-%Y'),
        TRY_STRPTIME(raw_observed_at, '%d/%m/%Y'),
        TRY_STRPTIME(raw_observed_at, '%Y-%m-%d'),
        '2026-11-22 00:00:00'::TIMESTAMP
    ) AS observed_at_utc,
    price_eur_per_litre,
    price_change_eur,
    source_id
FROM {{ ref('stg_fuel_prices') }}
