-- Staging: Extraction brute des sorties culturelles Echo.lu depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/culture_echo_lu/latest.json.gz')
)
SELECT
    raw_source.title::VARCHAR AS title,
    raw_source.start_date::VARCHAR AS raw_start_date,
    raw_source.end_date::VARCHAR AS raw_end_date,
    raw_source.venue::VARCHAR AS venue,
    raw_source.city::VARCHAR AS raw_city,
    raw_source.category::VARCHAR AS category,
    raw_source.source_url::VARCHAR AS source_url,
    'culture_echo_lu' AS source_id
FROM raw_source
