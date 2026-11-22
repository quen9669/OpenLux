-- Staging: Extraction brute des parcs de recyclage depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/recycling_centers/**/*.json.gz', union_by_name = true)
)
SELECT DISTINCT
    item_id::VARCHAR AS item_id,
    'RECYCLING_CENTER' AS category,
    name::VARCHAR AS name,
    schedule::VARCHAR AS status_or_schedule,
    details::VARCHAR AS details,
    observed_at::VARCHAR AS raw_observed_at,
    CURRENT_TIMESTAMP AS collected_at_utc,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_name::VARCHAR AS raw_commune_name,
    'recycling_centers' AS source_id
FROM raw_source
