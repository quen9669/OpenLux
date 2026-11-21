-- Silver: Consolidation des avis de grèves, débrayages et manifestations syndicales
WITH raw_strikes AS (
    SELECT * FROM {{ ref('stg_strikes_rss_lu') }}
),
ref_communes AS (
    SELECT * FROM {{ ref('ref_communes_lu') }} WHERE code_lau = 'LU0201'
)
SELECT
    s.strike_id,
    s.title,
    TRY_CAST(s.raw_published_at AS TIMESTAMP) AS published_at_utc,
    s.sector,
    s.country_code,
    s.country_name,
    s.source_url,
    'LU0201' AS commune_lau,
    c.canton,
    c.lat,
    c.lon,
    s.source_id
FROM raw_strikes s
LEFT JOIN ref_communes c ON c.code_lau = 'LU0201'
