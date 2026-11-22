-- Staging: Extraction brute des transports nationaux Mobiliteit.lu depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/transit_mobiliteit/latest.json.gz')
)
SELECT
    line_id::VARCHAR AS line_id,
    network::VARCHAR AS network,
    delay_seconds::INTEGER AS delay_seconds,
    disruption_level::VARCHAR AS disruption_level,
    message::VARCHAR AS message,
    observed_at::VARCHAR AS raw_observed_at,
    CURRENT_TIMESTAMP AS collected_at_utc,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_name::VARCHAR AS raw_commune_name,
    'transit_mobiliteit' AS source_id
FROM raw_source
