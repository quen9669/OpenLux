-- Staging agenda culturel : echo.lu, agenda Ville de Luxembourg, Rockhal
{% set cols = {'event_id': 'VARCHAR', 'title': 'VARCHAR', 'start_utc': 'VARCHAR', 'end_utc': 'VARCHAR', 'venue': 'VARCHAR', 'category': 'VARCHAR', 'is_free': 'BOOLEAN', 'price_min_eur': 'DOUBLE', 'commune_slug': 'VARCHAR', 'url': 'VARCHAR', 'lat': 'DOUBLE', 'lon': 'DOUBLE'} %}
SELECT * FROM {{ bronze('culture_echo_lu', cols) }}
UNION ALL BY NAME
SELECT * FROM {{ bronze('events_vdl_agenda', cols) }}
UNION ALL BY NAME
SELECT * FROM {{ bronze('events_rockhal', cols) }}
