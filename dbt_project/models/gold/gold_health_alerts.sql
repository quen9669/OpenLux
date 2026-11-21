-- Gold: Data Mart final des alertes sanitaires, pollens et défibrillateurs
SELECT
    record_id,
    record_type,
    headline_or_name,
    status_or_severity,
    metric_value,
    observed_at_utc,
    lat,
    lon,
    commune_lau,
    canton,
    source_id
FROM {{ ref('silver_health_alerts') }}
