-- Staging: Extraction brute des manifestations Stade de Luxembourg et Coque depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/venues_stade_coque/latest.json.gz')
)
SELECT
    raw_source.title::VARCHAR AS title,
    raw_source.start_date::VARCHAR AS raw_start_date,
    raw_source.end_date::VARCHAR AS raw_end_date,
    raw_source.venue::VARCHAR AS venue,
    raw_source.city::VARCHAR AS raw_city,
    raw_source.category::VARCHAR AS category,
    raw_source.source_url::VARCHAR AS source_url,
    'venues_stade_coque' AS source_id
FROM raw_source
