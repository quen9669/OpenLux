-- Staging: Extraction brute des statistiques chômage ADEM depuis Bronze
WITH raw_source AS (
    SELECT *
    FROM read_csv('data/bronze/unemployment_adem/**/*.csv.gz', header = true, union_by_name = true)
)
SELECT DISTINCT
    reference_month::VARCHAR AS reference_month,
    commune_name::VARCHAR AS raw_commune_name,
    jobseekers_count::INTEGER AS jobseekers_count,
    unemployment_rate_pct::DOUBLE AS unemployment_rate_pct,
    youth_unemployed_count::INTEGER AS youth_unemployed_count,
    'unemployment_adem' AS source_id
FROM raw_source
