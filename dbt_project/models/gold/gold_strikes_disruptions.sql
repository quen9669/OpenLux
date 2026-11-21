-- Gold: Data Mart final des préavis de grèves et manifestations
SELECT
    strike_id,
    title,
    published_at_utc,
    sector,
    country_code,
    country_name,
    source_url,
    commune_lau,
    canton,
    lat,
    lon,
    source_id
FROM {{ ref('silver_strikes_disruptions') }}
