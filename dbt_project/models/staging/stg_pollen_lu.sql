-- Staging: Extraction brute des concentrations polliniques depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/pollen_lu/latest.json.gz')
)
SELECT
    raw_source.specie::VARCHAR AS specie,
    raw_source.risk_level::VARCHAR AS risk_level,
    raw_source.grains_m3::INTEGER AS grains_m3,
    raw_source.observed_at::VARCHAR AS raw_observed_at,
    raw_source.station_name::VARCHAR AS station_name,
    raw_source.commune_name::VARCHAR AS raw_commune_name,
    'pollen_lu' AS source_id
FROM raw_source
