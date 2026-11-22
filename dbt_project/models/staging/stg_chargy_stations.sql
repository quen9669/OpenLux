-- Staging: Extraction brute des bornes Chargy depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/chargy_stations/**/*.json.gz', union_by_name = true)
)
SELECT DISTINCT
    facility_id::VARCHAR AS station_id,
    facility_name::VARCHAR AS station_name,
    CASE
        WHEN facility_name LIKE '%SuperChargy%' THEN 'SuperChargy'
        ELSE 'Chargy'
    END AS network_operator,
    COALESCE(available_points::INTEGER, 0) AS available_charging_points,
    COALESCE(total_points::INTEGER, 2) AS total_charging_points,
    '24/7' AS opening_hours,
    observed_at::VARCHAR AS raw_observed_at,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_name::VARCHAR AS raw_commune_name,
    'chargy_stations' AS source_id
FROM raw_source
WHERE facility_name IS NOT NULL
