-- Silver: Typage strict et normalisation temporelle de l'inflation et IPCN STATEC
SELECT
    reference_month,
    TRY_CAST(raw_observed_at AS TIMESTAMP) AS observed_at_utc,
    ipcn_index,
    inflation_annual_rate,
    wage_index_quote,
    source_id
FROM {{ ref('stg_statec_inflation') }}
