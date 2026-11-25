-- Staging aéronefs OpenSky au-dessus du Luxembourg
{% set cols = {'icao24': 'VARCHAR', 'callsign': 'VARCHAR', 'origin_country': 'VARCHAR', 'observed_at': 'VARCHAR', 'baro_altitude_m': 'DOUBLE', 'on_ground': 'BOOLEAN', 'velocity_ms': 'DOUBLE', 'lat': 'DOUBLE', 'lon': 'DOUBLE'} %}
SELECT * FROM {{ bronze('aviation_opensky', cols) }}
