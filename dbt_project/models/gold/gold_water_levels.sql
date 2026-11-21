-- Gold: Data Mart final des niveaux d'eau et crues des rivières au Luxembourg
SELECT
    station_id,
    station_name,
    river_name,
    observed_at_utc,
    water_level_cm,
    discharge_m3s,
    alert_level,
    lat,
    lon,
    commune_lau,
    canton,
    source_id
FROM {{ ref('silver_water_levels') }}
