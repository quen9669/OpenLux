-- Staging: Extraction brute des autobus AVL temps réel depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/transit_avl_rt/**/*.json.gz', union_by_name = true)
)
SELECT DISTINCT
    line_id::VARCHAR AS line_id,
    network::VARCHAR AS network,
    delay_seconds::INTEGER AS delay_seconds,
    disruption_level::VARCHAR AS disruption_level,
    message::VARCHAR AS message,
    observed_at::VARCHAR AS raw_observed_at,
    COALESCE(TRY_CAST(observed_at AS TIMESTAMP), '2026-11-20 22:00:00'::TIMESTAMP) AS collected_at_utc,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_name::VARCHAR AS raw_commune_name,
    'transit_avl_rt' AS source_id
FROM raw_source
