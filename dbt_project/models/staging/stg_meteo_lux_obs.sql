-- Staging: Extraction brute incrémentale des observations météo depuis la couche Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/meteo_lux_obs/**/*.json.gz', union_by_name = true)
)
SELECT DISTINCT
    station_id::VARCHAR AS station_id,
    station_name::VARCHAR AS station_name,
    timestamp::VARCHAR AS raw_timestamp,
    temperature::DOUBLE AS temperature,
    humidity::DOUBLE AS humidity,
    pressure_hpa::DOUBLE AS pressure_hpa,
    wind_speed_kmh::DOUBLE AS wind_speed_kmh,
    precipitation_mm::DOUBLE AS precipitation_mm,
    condition::VARCHAR AS weather_condition,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_lau::VARCHAR AS commune_lau,
    'meteo_lux_obs' AS source_id
FROM raw_source
