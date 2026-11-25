-- Staging eaux de baignade : statut courant (collection 656) et classe de qualité (581)
{% set cols = {'site_id': 'VARCHAR', 'site_name': 'VARCHAR', 'bathing_status': 'VARCHAR', 'quality_class': 'VARCHAR', 'profile_url': 'VARCHAR', 'lat': 'DOUBLE', 'lon': 'DOUBLE'} %}
SELECT * FROM {{ bronze('bathing_status_age', cols) }}
UNION ALL BY NAME
SELECT * FROM {{ bronze('bathing_quality_age', cols) }}
