-- Staging: Extraction brute des événements DATEX II CITA depuis la couche Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/traffic_cita_datex2/latest.json.gz')
)
SELECT
    event_id::VARCHAR AS event_id,
    road_name::VARCHAR AS road_name,
    situation_type::VARCHAR AS situation_type,
    start_time::VARCHAR AS raw_start_time,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    comment::VARCHAR AS traffic_comment,
    'traffic_cita_datex2' AS source_id
FROM raw_source
