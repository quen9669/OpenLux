-- Silver: Consolidation des avis de grèves, débrayages et manifestations syndicales
WITH raw_strikes AS (
    SELECT * FROM {{ ref('stg_strikes_rss_lu') }}
)
SELECT
    s.strike_id,
    s.title,
    COALESCE(
        TRY_STRPTIME(
            REGEXP_EXTRACT(s.raw_published_at, '([0-9]{1,2} [A-Za-z]{3} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2})'),
            '%d %b %Y %H:%M:%S'
        ),
        TRY_CAST(s.raw_published_at AS TIMESTAMP)
    ) AS published_at_utc,
    s.sector,
    s.country_code,
    s.country_name,
    s.source_url,
    s.source_id
FROM raw_strikes s
