-- Gold vigilances météo (MeteoLux via MeteoAlarm)
SELECT
    * EXCLUDE (onset_utc, expires_utc, observed_at),
    {{ utc('onset_utc') }} AS onset_utc, {{ utc('expires_utc') }} AS expires_utc, {{ utc('observed_at') }} AS sent_utc
FROM {{ ref('stg_weather_warnings') }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY alert_id, area ORDER BY collected_at_utc DESC) = 1
