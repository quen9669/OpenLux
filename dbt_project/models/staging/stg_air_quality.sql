-- Staging: Extraction brute de la qualité de l'air depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/air_quality_lu/**/*.json.gz', union_by_name = true)
)
SELECT DISTINCT
    station_id::VARCHAR AS station_id,
    station_name::VARCHAR AS station_name,
    observed_at::VARCHAR AS raw_observed_at,
    pollutant::VARCHAR AS pollutant,
    value::DOUBLE AS pollutant_value,
    unit::VARCHAR AS unit,
    aqi_index::VARCHAR AS aqi_index,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_lau::VARCHAR AS commune_lau,
    'air_quality_lu' AS source_id
FROM raw_source
WHERE station_id IS NOT NULL
