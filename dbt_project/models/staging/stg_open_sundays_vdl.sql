-- Staging: Extraction brute des ouvertures dominicales VDL depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/open_sundays_vdl/latest.json.gz')
)
SELECT
    item_id::VARCHAR AS item_id,
    'OPEN_SUNDAY' AS category,
    name::VARCHAR AS name,
    schedule::VARCHAR AS status_or_schedule,
    details::VARCHAR AS details,
    observed_at::VARCHAR AS raw_observed_at,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_name::VARCHAR AS raw_commune_name,
    'open_sundays_vdl' AS source_id
FROM raw_source
