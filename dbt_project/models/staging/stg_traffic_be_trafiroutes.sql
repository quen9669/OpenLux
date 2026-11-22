-- Staging: Extraction brute du trafic frontalier E411 Belgique depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/traffic_be_trafiroutes/latest.json.gz')
)
SELECT
    event_id::VARCHAR AS event_id,
    corridor::VARCHAR AS corridor,
    'ROAD' AS transport_mode,
    delay_minutes::DOUBLE AS delay_minutes,
    status::VARCHAR AS status,
    comment::VARCHAR AS comment,
    observed_at::VARCHAR AS raw_observed_at,
    CURRENT_TIMESTAMP AS collected_at_utc,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_name::VARCHAR AS raw_commune_name,
    'traffic_be_trafiroutes' AS source_id
FROM raw_source
