-- Staging perturbations transports publics (bus VdL, SNCF, SNCB)
{% set cols = {'disruption_id': 'VARCHAR', 'operator': 'VARCHAR', 'mode': 'VARCHAR', 'title': 'VARCHAR', 'severity': 'VARCHAR', 'category': 'VARCHAR', 'start_time_utc': 'VARCHAR', 'end_time_utc': 'VARCHAR', 'observed_at': 'VARCHAR', 'detail': 'VARCHAR'} %}
SELECT * FROM {{ bronze('bus_vdl_messages', cols) }}
UNION ALL BY NAME
SELECT * FROM {{ bronze('rail_sncf_siri', cols) }}
UNION ALL BY NAME
SELECT * FROM {{ bronze('rail_sncb_irail', cols) }}
