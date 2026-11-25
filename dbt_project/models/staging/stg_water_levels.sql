-- Staging niveaux d'eau AGE (15 min), positions issues du seed officiel des stations
{% set cols = {'station_name': 'VARCHAR', 'observed_at': 'VARCHAR', 'water_level': 'DOUBLE', 'unit': 'VARCHAR'} %}
SELECT w.*, s.lat, s.lon
FROM {{ bronze('water_levels_age', cols) }} w
LEFT JOIN {{ ref('ref_water_stations') }} s USING (station_name)
