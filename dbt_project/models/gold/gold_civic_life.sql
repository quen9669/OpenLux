-- Gold: Data Mart final des pétitions citoyennes et statistiques de l'emploi
SELECT
    record_id,
    record_type,
    title_or_indicator,
    signatures_count,
    rate_value,
    status,
    observed_at_utc,
    lat,
    lon,
    commune_lau,
    canton,
    source_id
FROM {{ ref('silver_civic_life') }}
