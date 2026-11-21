-- Staging: Extraction brute des pistes cyclables nationales depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/bike_lanes_lu/latest.json.gz')
)
SELECT
    item_id::VARCHAR AS item_id,
    'BIKE_LANE' AS category,
    name::VARCHAR AS name,
    status::VARCHAR AS status_or_schedule,
    details::VARCHAR AS details,
    observed_at::VARCHAR AS raw_observed_at,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_name::VARCHAR AS raw_commune_name,
    'bike_lanes_lu' AS source_id
FROM raw_source
