-- Staging: Extraction brute des zones de bruit stratégiques depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/noise_zones_lu/**/*.json.gz', union_by_name = true)
)
SELECT DISTINCT
    zone_id::VARCHAR AS record_id,
    'NOISE_CONTOUR' AS record_type,
    zone_name::VARCHAR AS callsign_or_zone,
    noise_level_dba::DOUBLE AS altitude_m_or_dba,
    noise_indicator::VARCHAR AS status,
    observed_at::VARCHAR AS raw_observed_at,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_name::VARCHAR AS raw_commune_name,
    'noise_zones_lu' AS source_id
FROM raw_source
