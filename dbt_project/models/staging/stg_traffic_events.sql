-- Staging événements trafic LU (CITA, Ville) et frontaliers (DIR Est, Autobahn)
{% set cols = {'event_id': 'VARCHAR', 'country_code': 'VARCHAR', 'road_name': 'VARCHAR', 'situation_type': 'VARCHAR', 'situation_subtype': 'VARCHAR', 'validity_status': 'VARCHAR', 'start_time_utc': 'VARCHAR', 'end_time_utc': 'VARCHAR', 'observed_at': 'VARCHAR', 'description': 'VARCHAR', 'lat': 'DOUBLE', 'lon': 'DOUBLE'} %}
SELECT * FROM {{ bronze('traffic_cita_datex2', cols) }}
UNION ALL BY NAME
SELECT * FROM {{ bronze('traffic_vdl_info', cols) }}
UNION ALL BY NAME
SELECT * FROM {{ bronze('traffic_fr_dir_est', cols) }}
UNION ALL BY NAME
SELECT * FROM {{ bronze('traffic_de_a1', cols) }}
UNION ALL BY NAME
SELECT * FROM {{ bronze('traffic_de_a8', cols) }}
UNION ALL BY NAME
SELECT * FROM {{ bronze('traffic_de_a64', cols) }}
