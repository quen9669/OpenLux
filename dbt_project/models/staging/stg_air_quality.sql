-- Staging qualité de l'air et pollens (modèle CAMS via Open-Meteo), format long
{% set cols = {'station_id': 'VARCHAR', 'location_index': 'INTEGER', 'observed_at': 'VARCHAR', 'pollutant': 'VARCHAR', 'value': 'DOUBLE', 'unit': 'VARCHAR', 'lat': 'DOUBLE', 'lon': 'DOUBLE'} %}
-- POURQUOI : points modèle rattachés au chef-lieu demandé (grid_lat/grid_lon = maille réelle)
SELECT
    m.* EXCLUDE (lat, lon), m.lat AS grid_lat, m.lon AS grid_lon,
    COALESCE(p.point_name, NULL) AS point_name,
    COALESCE(c.lat, m.lat) AS lat, COALESCE(c.lon, m.lon) AS lon
FROM (SELECT * FROM {{ bronze('air_quality_openmeteo', cols) }}
UNION ALL BY NAME
SELECT * FROM {{ bronze('pollen_openmeteo', cols) }}) m
LEFT JOIN {{ ref('ref_model_points') }} p USING (location_index)
LEFT JOIN {{ ref('ref_communes_lu') }} c ON c.code_lau = p.code_lau
