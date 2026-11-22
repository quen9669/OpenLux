-- Staging: Extraction brute des autorisations de bâtir STATEC depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/housing_statec/**/*.json.gz', union_by_name = true)
)
SELECT DISTINCT
    record_id::VARCHAR AS record_id,
    commune_name::VARCHAR AS raw_commune_name,
    canton_name::VARCHAR AS canton_name,
    property_type::VARCHAR AS property_type,
    reference_period::VARCHAR AS reference_period,
    permits_count::INTEGER AS permits_count,
    units_authorized::INTEGER AS units_authorized,
    observed_at::VARCHAR AS raw_observed_at,
    'housing_statec' AS source_id
FROM raw_source
WHERE record_id IS NOT NULL
