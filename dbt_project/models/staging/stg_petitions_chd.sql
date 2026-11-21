-- Staging: Extraction brute des pétitions publiques CHD depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_json_auto('data/bronze/petitions_chd/latest.json.gz')
)
SELECT
    raw_source.petition_id::VARCHAR AS petition_id,
    raw_source.title::VARCHAR AS title,
    raw_source.signatures_count::INTEGER AS signatures_count,
    raw_source.threshold_met::BOOLEAN AS threshold_met,
    raw_source.status::VARCHAR AS status,
    raw_source.deposited_at::VARCHAR AS raw_deposited_at,
    raw_source.closed_at::VARCHAR AS raw_closed_at,
    raw_source.source_url::VARCHAR AS source_url,
    'petitions_chd' AS source_id
FROM raw_source
