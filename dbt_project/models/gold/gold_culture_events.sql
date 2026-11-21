-- Gold: Data Mart final des événements culturels, spectacles et salons
SELECT
    title,
    start_date,
    end_date,
    venue,
    category,
    source_url,
    commune_lau,
    canton,
    lat,
    lon,
    source_id
FROM {{ ref('silver_culture_events') }}
