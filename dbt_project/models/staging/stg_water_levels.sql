-- Staging: Extraction brute des niveaux d'eau et crues depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/water_levels_lu/**/*.json.gz', union_by_name = true)
)
SELECT DISTINCT
    station_id::VARCHAR AS station_id,
    station_name::VARCHAR AS station_name,
    river_name::VARCHAR AS river_name,
    observed_at::VARCHAR AS raw_observed_at,
    CURRENT_TIMESTAMP AS collected_at_utc,
    water_level_cm::DOUBLE AS water_level_cm,
    discharge_m3s::DOUBLE AS discharge_m3s,
    alert_level::VARCHAR AS alert_level,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_lau::VARCHAR AS commune_lau,
    'water_levels_lu' AS source_id
FROM raw_source
