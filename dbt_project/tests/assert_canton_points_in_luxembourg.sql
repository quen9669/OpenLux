-- Tout point rattaché à un canton doit être dans l'emprise du Luxembourg : 0 ligne attendue
SELECT 'gold_weather_observations' AS gold_table, lat, lon, canton FROM {{ ref('gold_weather_observations') }} WHERE canton IS NOT NULL AND (lat NOT BETWEEN 49.40 AND 50.20 OR lon NOT BETWEEN 5.70 AND 6.55)
UNION ALL
SELECT 'gold_air_quality' AS gold_table, lat, lon, canton FROM {{ ref('gold_air_quality') }} WHERE canton IS NOT NULL AND (lat NOT BETWEEN 49.40 AND 50.20 OR lon NOT BETWEEN 5.70 AND 6.55)
UNION ALL
SELECT 'gold_water_levels' AS gold_table, lat, lon, canton FROM {{ ref('gold_water_levels') }} WHERE canton IS NOT NULL AND (lat NOT BETWEEN 49.40 AND 50.20 OR lon NOT BETWEEN 5.70 AND 6.55)
UNION ALL
SELECT 'gold_bathing_water' AS gold_table, lat, lon, canton FROM {{ ref('gold_bathing_water') }} WHERE canton IS NOT NULL AND (lat NOT BETWEEN 49.40 AND 50.20 OR lon NOT BETWEEN 5.70 AND 6.55)
UNION ALL
SELECT 'gold_traffic_events' AS gold_table, lat, lon, canton FROM {{ ref('gold_traffic_events') }} WHERE canton IS NOT NULL AND (lat NOT BETWEEN 49.40 AND 50.20 OR lon NOT BETWEEN 5.70 AND 6.55)
UNION ALL
SELECT 'gold_roadworks' AS gold_table, lat, lon, canton FROM {{ ref('gold_roadworks') }} WHERE canton IS NOT NULL AND (lat NOT BETWEEN 49.40 AND 50.20 OR lon NOT BETWEEN 5.70 AND 6.55)
UNION ALL
SELECT 'gold_mobility_veloh' AS gold_table, lat, lon, canton FROM {{ ref('gold_mobility_veloh') }} WHERE canton IS NOT NULL AND (lat NOT BETWEEN 49.40 AND 50.20 OR lon NOT BETWEEN 5.70 AND 6.55)
UNION ALL
SELECT 'gold_mobility_parkings' AS gold_table, lat, lon, canton FROM {{ ref('gold_mobility_parkings') }} WHERE canton IS NOT NULL AND (lat NOT BETWEEN 49.40 AND 50.20 OR lon NOT BETWEEN 5.70 AND 6.55)
UNION ALL
SELECT 'gold_chargy_stations' AS gold_table, lat, lon, canton FROM {{ ref('gold_chargy_stations') }} WHERE canton IS NOT NULL AND (lat NOT BETWEEN 49.40 AND 50.20 OR lon NOT BETWEEN 5.70 AND 6.55)
UNION ALL
SELECT 'gold_equipment' AS gold_table, lat, lon, canton FROM {{ ref('gold_equipment') }} WHERE canton IS NOT NULL AND (lat NOT BETWEEN 49.40 AND 50.20 OR lon NOT BETWEEN 5.70 AND 6.55)
UNION ALL
SELECT 'gold_culture_events' AS gold_table, lat, lon, canton FROM {{ ref('gold_culture_events') }} WHERE canton IS NOT NULL AND (lat NOT BETWEEN 49.40 AND 50.20 OR lon NOT BETWEEN 5.70 AND 6.55)
