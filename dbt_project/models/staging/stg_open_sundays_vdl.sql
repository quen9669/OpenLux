-- Staging: Extraction brute des ouvertures dominicales VDL depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/open_sundays_vdl/**/*.json.gz', union_by_name = true)
)
SELECT DISTINCT
    item_id::VARCHAR AS item_id,
    'OPEN_SUNDAY' AS category,
    name::VARCHAR AS name,
    schedule::VARCHAR AS status_or_schedule,
    details::VARCHAR AS details,
    observed_at::VARCHAR AS raw_observed_at,
    COALESCE(TRY_CAST(observed_at AS TIMESTAMP), '2026-01-01 00:00:00'::TIMESTAMP) AS collected_at_utc,
    lat::DOUBLE AS lat,
    lon::DOUBLE AS lon,
    commune_name::VARCHAR AS raw_commune_name,
    'open_sundays_vdl' AS source_id
FROM raw_source
