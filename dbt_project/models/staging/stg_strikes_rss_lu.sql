-- Staging: Extraction brute des avis de grèves et manifestations depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/strikes_rss_lu/**/*.json.gz', union_by_name = true)
)
SELECT DISTINCT
    raw_source.strike_id::VARCHAR AS strike_id,
    raw_source.title::VARCHAR AS title,
    raw_source.published_at::VARCHAR AS raw_published_at,
    raw_source.source_url::VARCHAR AS source_url,
    raw_source.sector::VARCHAR AS sector,
    COALESCE(raw_source.country_code::VARCHAR, 'LU') AS country_code,
    COALESCE(raw_source.country_name::VARCHAR, 'Luxembourg') AS country_name,
    'strikes_rss_lu' AS source_id
FROM raw_source
WHERE raw_source.title IS NOT NULL
