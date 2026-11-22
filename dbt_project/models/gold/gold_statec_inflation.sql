-- Gold: Data Mart final de l'inflation IPCN et cote d'application STATEC
SELECT
    reference_month,
    observed_at_utc,
    ipcn_index,
    inflation_annual_rate,
    wage_index_quote,
    source_id
FROM {{ ref('silver_statec_inflation') }}
WHERE reference_month IS NOT NULL
  AND ipcn_index IS NOT NULL
