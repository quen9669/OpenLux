-- Staging: Extraction brute des événements DATEX II CITA depuis la couche Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/traffic_cita_datex2/**/*.json.gz', union_by_name = true)
)
SELECT DISTINCT
    event_id::VARCHAR AS event_id,
    road_name::VARCHAR AS road_name,
    situation_type::VARCHAR AS situation_type,
    start_time::VARCHAR AS raw_start_time,
    CURRENT_TIMESTAMP AS collected_at_utc,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_name::VARCHAR AS raw_commune_name,
    comment::VARCHAR AS traffic_comment,
    'traffic_cita_datex2' AS source_id
FROM raw_source
