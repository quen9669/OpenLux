-- Staging: Extraction brute du trafic frontalier A31 France depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/traffic_fr_bisonfute/**/*.json.gz', union_by_name = true)
)
SELECT DISTINCT
    event_id::VARCHAR AS event_id,
    corridor::VARCHAR AS corridor,
    'ROAD' AS transport_mode,
    delay_minutes::DOUBLE AS delay_minutes,
    status::VARCHAR AS status,
    comment::VARCHAR AS comment,
    observed_at::VARCHAR AS raw_observed_at,
    COALESCE(TRY_CAST(observed_at AS TIMESTAMP), '2026-11-20 22:00:00'::TIMESTAMP) AS collected_at_utc,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_name::VARCHAR AS raw_commune_name,
    'traffic_fr_bisonfute' AS source_id
FROM raw_source
