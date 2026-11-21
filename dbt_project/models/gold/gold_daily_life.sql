-- Gold: Data Mart final des pistes cyclables, commerces ouverts et centres de recyclage
SELECT
    item_id,
    category,
    name,
    observed_at_utc,
    status_or_schedule,
    details,
    lat,
    lon,
    commune_lau,
    canton,
    source_id
FROM {{ ref('silver_daily_life') }}
