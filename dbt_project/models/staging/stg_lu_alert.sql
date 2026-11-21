-- Staging: Extraction brute des messages d'urgence LU-Alert depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/lu_alert/latest.json.gz')
)
SELECT
    raw_source.alert_id::VARCHAR AS alert_id,
    raw_source.headline::VARCHAR AS headline,
    raw_source.severity::VARCHAR AS severity,
    raw_source.certainty::VARCHAR AS certainty,
    raw_source.effective_utc::VARCHAR AS raw_effective_utc,
    raw_source.expires_utc::VARCHAR AS raw_expires_utc,
    raw_source.area_desc::VARCHAR AS area_desc,
    raw_source.commune_name::VARCHAR AS raw_commune_name,
    'lu_alert' AS source_id
FROM raw_source
