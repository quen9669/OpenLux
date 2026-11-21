-- Staging: Extraction brute des avis de grèves et manifestations depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/strikes_rss_lu/latest.json.gz')
)
SELECT
    raw_source.strike_id::VARCHAR AS strike_id,
    raw_source.title::VARCHAR AS title,
    raw_source.published_at::VARCHAR AS raw_published_at,
    raw_source.source_url::VARCHAR AS source_url,
    raw_source.sector::VARCHAR AS sector,
    'strikes_rss_lu' AS source_id
FROM raw_source
