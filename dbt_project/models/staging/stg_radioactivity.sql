-- Staging: Extraction brute de la surveillance radiologique depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/radioactivity_lu/latest.json.gz')
)
SELECT
    station_id::VARCHAR AS station_id,
    station_name::VARCHAR AS station_name,
    observed_at::VARCHAR AS raw_observed_at,
    dose_rate_nsvh::DOUBLE AS dose_rate_nsvh,
    status::VARCHAR AS radiological_status,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_lau::VARCHAR AS commune_lau,
    'radioactivity_lu' AS source_id
FROM raw_source
