-- Gold: Data Mart final des événements culturels, spectacles et salons
SELECT
    title,
    status,
    start_date,
    end_date,
    observed_at_utc,
    start_time,
    venue,
    address,
    category,
    price_eur,
    price_text,
    is_free,
    source_url,
    ticket_url,
    commune_lau,
    canton,
    lat,
    lon,
    source_id
FROM {{ ref('silver_culture_events') }}
