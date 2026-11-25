-- Staging demandeurs d'emploi ADEM par commune et sexe
{% set cols = {'reference_month': 'VARCHAR', 'commune_name': 'VARCHAR', 'canton': 'VARCHAR', 'sex': 'VARCHAR', 'job_seekers': 'DOUBLE'} %}
SELECT * FROM {{ bronze('unemployment_adem', cols) }}
