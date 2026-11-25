-- Staging chantiers : Ponts et Chaussées (DATEX II) et Ville de Luxembourg (ArcGIS)
{% set dx = {'event_id': 'VARCHAR', 'road_name': 'VARCHAR', 'situation_subtype': 'VARCHAR', 'start_time_utc': 'VARCHAR', 'end_time_utc': 'VARCHAR', 'description': 'VARCHAR', 'lat': 'DOUBLE', 'lon': 'DOUBLE'} %}
{% set vdl = {'work_id': 'VARCHAR', 'authority': 'VARCHAR', 'road_name': 'VARCHAR', 'title': 'VARCHAR', 'contractor': 'VARCHAR', 'start_time_utc': 'VARCHAR', 'end_time_utc': 'VARCHAR', 'lat': 'DOUBLE', 'lon': 'DOUBLE'} %}
SELECT
    event_id AS work_id, 'Administration des ponts et chaussées' AS authority, road_name,
    description AS title, situation_subtype AS work_type, NULL::VARCHAR AS contractor,
    start_time_utc, end_time_utc, lat, lon, collected_at_utc, source_id
FROM {{ bronze('roadworks_cita_current', dx) }}
UNION ALL BY NAME
SELECT
    event_id AS work_id, 'Administration des ponts et chaussées' AS authority, road_name,
    description AS title, situation_subtype AS work_type, NULL::VARCHAR AS contractor,
    start_time_utc, end_time_utc, lat, lon, collected_at_utc, source_id
FROM {{ bronze('roadworks_cita_planned', dx) }}
UNION ALL BY NAME
SELECT *, NULL::VARCHAR AS work_type FROM {{ bronze('roadworks_vdl', vdl) }}
UNION ALL BY NAME
SELECT *, NULL::VARCHAR AS work_type FROM {{ bronze('roadworks_vdl_permits', vdl) }}
