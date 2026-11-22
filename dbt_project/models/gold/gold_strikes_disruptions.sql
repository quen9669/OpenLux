-- Gold: Data Mart final des avis de grèves et mouvements sociaux
SELECT
    strike_id,
    title,
    published_at_utc,
    sector,
    country_code,
    country_name,
    source_url,
    source_id
FROM {{ ref('silver_strikes_disruptions') }}
