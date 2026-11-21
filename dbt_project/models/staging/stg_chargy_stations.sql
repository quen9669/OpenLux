-- Staging: Extraction brute des bornes Chargy depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/chargy_stations/latest.json.gz')
)
SELECT
    facility_id::VARCHAR AS facility_id,
    'CHARGY' AS facility_type,
    facility_name::VARCHAR AS facility_name,
    available_points::INTEGER AS available_capacity,
    total_points::INTEGER AS total_capacity,
    '24/7' AS opening_hours,
    observed_at::VARCHAR AS raw_observed_at,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_name::VARCHAR AS raw_commune_name,
    'chargy_stations' AS source_id
FROM raw_source
