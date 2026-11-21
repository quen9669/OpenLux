-- Staging: Extraction brute de la qualité des eaux de baignade depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_csv('data/bronze/bathing_water_lu/latest.csv.gz', header = true)
)
SELECT
    site_id::VARCHAR AS site_id,
    site_name::VARCHAR AS site_name,
    water_body::VARCHAR AS water_body,
    inspection_date::VARCHAR AS raw_inspection_date,
    quality_class::VARCHAR AS quality_class,
    cyanobacteria_bloom::VARCHAR AS cyanobacteria_bloom,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_name::VARCHAR AS raw_commune_name,
    'bathing_water_lu' AS source_id
FROM raw_source
