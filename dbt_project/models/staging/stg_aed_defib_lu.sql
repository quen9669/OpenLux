-- Staging: Extraction brute des défibrillateurs AED depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_csv('data/bronze/aed_defib_lu/latest.csv.gz', header = true)
)
SELECT
    aed_id::VARCHAR AS aed_id,
    location_name::VARCHAR AS location_name,
    street::VARCHAR AS street,
    postal_code::VARCHAR AS postal_code,
    commune_name::VARCHAR AS raw_commune_name,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    access_hours::VARCHAR AS access_hours,
    'aed_defib_lu' AS source_id
FROM raw_source
