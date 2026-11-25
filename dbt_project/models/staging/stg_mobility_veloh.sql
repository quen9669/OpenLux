-- Staging Vel'oh (JCDecaux v3 ou GBFS) ; nom, adresse et capacité du seed officiel GBFS
{% set cols = {'station_number': 'INTEGER', 'observed_at': 'VARCHAR', 'available_bikes': 'INTEGER', 'available_electrical_bikes': 'INTEGER', 'available_mechanical_bikes': 'INTEGER', 'available_stands': 'INTEGER', 'disabled_bikes': 'INTEGER', 'disabled_stands': 'INTEGER', 'is_renting': 'BOOLEAN', 'lat': 'DOUBLE', 'lon': 'DOUBLE'} %}
SELECT
    v.* EXCLUDE (lat, lon), r.station_name, r.address, r.capacity,
    COALESCE(v.lat, r.lat) AS lat, COALESCE(v.lon, r.lon) AS lon
FROM {{ bronze('veloh_stations', cols) }} v
LEFT JOIN {{ ref('ref_veloh_stations') }} r USING (station_number)
