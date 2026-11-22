-- Staging: Extraction brute des vols OpenSky Network depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/aviation_opensky_lu/**/*.json.gz', union_by_name = true)
)
SELECT DISTINCT
    icao24::VARCHAR AS record_id,
    'FLIGHT_MOVEMENT' AS record_type,
    callsign::VARCHAR AS callsign_or_zone,
    baro_altitude_m::DOUBLE AS altitude_m_or_dba,
    status::VARCHAR AS status,
    observed_at::VARCHAR AS raw_observed_at,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_name::VARCHAR AS raw_commune_name,
    'aviation_opensky_lu' AS source_id
FROM raw_source
WHERE icao24 IS NOT NULL
