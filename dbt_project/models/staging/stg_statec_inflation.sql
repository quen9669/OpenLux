-- Staging: Extraction brute de l'inflation et IPCN STATEC depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/statec_inflation/latest.json.gz')
)
SELECT
    reference_month::VARCHAR AS reference_month,
    observed_at::VARCHAR AS raw_observed_at,
    ipcn_index::DOUBLE AS ipcn_index,
    inflation_annual_rate::DOUBLE AS inflation_annual_rate,
    wage_index_quote::DOUBLE AS wage_index_quote,
    'statec_inflation' AS source_id
FROM raw_source
