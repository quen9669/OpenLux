-- Staging vigilances météo MeteoLux (flux MeteoAlarm)
{% set cols = {'alert_id': 'VARCHAR', 'event': 'VARCHAR', 'severity': 'VARCHAR', 'awareness_level': 'VARCHAR', 'area': 'VARCHAR', 'onset_utc': 'VARCHAR', 'expires_utc': 'VARCHAR', 'observed_at': 'VARCHAR'} %}
SELECT * FROM {{ bronze('weather_warnings_meteoalarm', cols) }}
