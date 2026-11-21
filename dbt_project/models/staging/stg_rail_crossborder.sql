-- Staging: Extraction brute des trains transfrontaliers depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/rail_crossborder/latest.json.gz')
)
SELECT
    event_id::VARCHAR AS event_id,
    corridor::VARCHAR AS corridor,
    'RAIL' AS transport_mode,
    delay_minutes::DOUBLE AS delay_minutes,
    status::VARCHAR AS status,
    comment::VARCHAR AS comment,
    observed_at::VARCHAR AS raw_observed_at,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_name::VARCHAR AS raw_commune_name,
    'rail_crossborder' AS source_id
FROM raw_source
