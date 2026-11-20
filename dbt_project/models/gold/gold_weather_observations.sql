-- Gold: Data Mart final des observations météo nationales luxembourgeoises
SELECT
    station_id,
    station_name,
    observed_at_utc,
    temperature,
    humidity,
    pressure_hpa,
    wind_speed_kmh,
    precipitation_mm,
    weather_condition,
    lat,
    lon,
    commune_lau,
    canton,
    source_id
FROM {{ ref('silver_weather_observations') }}
