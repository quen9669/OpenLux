-- Gold IPCN (STATEC) : indice et variation annuelle calculée sur 12 mois
WITH m AS (
    SELECT time_period AS reference_month, obs_value AS ipcn_index, base_period_label, collected_at_utc, source_id
    FROM {{ ref('stg_inflation') }} WHERE freq = 'M'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY time_period ORDER BY collected_at_utc DESC) = 1
)
SELECT
    *,
    ROUND(100.0 * (ipcn_index / LAG(ipcn_index, 12) OVER (ORDER BY reference_month) - 1), 2) AS annual_change_pct
FROM m
