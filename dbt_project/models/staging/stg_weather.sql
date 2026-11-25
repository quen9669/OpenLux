-- Staging météo : station officielle MeteoLux (Findel) + grille modèle Open-Meteo (12 cantons)
{% set cols = {'station_id': 'VARCHAR', 'station_name': 'VARCHAR', 'data_origin': 'VARCHAR', 'location_index': 'INTEGER', 'observed_at': 'VARCHAR', 'temperature_c': 'DOUBLE', 'humidity_pct': 'DOUBLE', 'pressure_hpa': 'DOUBLE', 'wind_speed_kmh': 'DOUBLE', 'precipitation_mm': 'DOUBLE', 'weather_code': 'INTEGER', 'lat': 'DOUBLE', 'lon': 'DOUBLE'} %}
-- POURQUOI : points modèle rattachés au chef-lieu demandé (grid_lat/grid_lon = maille réelle)
SELECT
    m.* EXCLUDE (lat, lon, station_name), m.lat AS grid_lat, m.lon AS grid_lon,
    COALESCE(p.point_name, m.station_name) AS station_name,
    COALESCE(c.lat, m.lat) AS lat, COALESCE(c.lon, m.lon) AS lon
FROM (SELECT * FROM {{ bronze('meteo_findel_meteolux', cols) }}
UNION ALL BY NAME
SELECT * FROM {{ bronze('meteo_cantons_openmeteo', cols) }}) m
LEFT JOIN {{ ref('ref_model_points') }} p USING (location_index)
LEFT JOIN {{ ref('ref_communes_lu') }} c ON c.code_lau = p.code_lau
