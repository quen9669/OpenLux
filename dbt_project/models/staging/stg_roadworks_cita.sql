-- Staging: Extraction brute des chantiers autoroutiers CITA depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/roadworks_cita/**/*.json.gz', union_by_name = true)
)
SELECT DISTINCT
    raw_source.work_id::VARCHAR AS work_id,
    'CITA' AS authority,
    raw_source.road_name::VARCHAR AS road_name,
    raw_source.start_date::VARCHAR AS raw_start_date,
    raw_source.end_date::VARCHAR AS raw_end_date,
    raw_source.impact_level::VARCHAR AS impact_level,
    raw_source.title::VARCHAR AS title,
    raw_source.observed_at::VARCHAR AS raw_observed_at,
    raw_source.lat::DOUBLE AS lat,
    raw_source.lon::DOUBLE AS lon,
    raw_source.commune_name::VARCHAR AS raw_commune_name,
    'roadworks_cita' AS source_id
FROM raw_source
