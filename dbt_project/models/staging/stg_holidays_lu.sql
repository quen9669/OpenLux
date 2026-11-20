-- Staging: Extraction brute du calendrier officiel luxembourgeois depuis la couche Bronze
WITH raw_source AS (
    SELECT *
    FROM read_csv('data/bronze/holidays_lu/latest.csv.gz', header=true)
)
SELECT
    date::VARCHAR AS raw_date,
    name::VARCHAR AS holiday_name_fr,
    name_de::VARCHAR AS holiday_name_de,
    name_lb::VARCHAR AS holiday_name_lb,
    is_legal_holiday::BOOLEAN AS is_legal_holiday,
    is_school_vacation::BOOLEAN AS is_school_vacation,
    'holidays_lu' AS source_id
FROM raw_source
