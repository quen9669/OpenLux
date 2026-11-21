-- Gold: Data Mart final des mesures de la qualité de l'air au Luxembourg
SELECT
    station_id,
    station_name,
    observed_at_utc,
    pollutant,
    pollutant_value,
    unit,
    aqi_index,
    lat,
    lon,
    commune_lau,
    canton,
    source_id
FROM {{ ref('silver_air_quality') }}
