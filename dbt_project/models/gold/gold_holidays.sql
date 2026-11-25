-- Gold jours fériés LU/FR/BE/DE et vacances scolaires LU
SELECT
    * EXCLUDE (holiday_date, end_date),
    CAST(holiday_date AS DATE) AS holiday_date,
    CAST(end_date AS DATE) AS end_date
FROM {{ ref('stg_holidays') }}
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY holiday_date, country_code, region_code, holiday_type ORDER BY collected_at_utc DESC
) = 1
