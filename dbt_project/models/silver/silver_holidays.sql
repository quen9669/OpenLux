-- Silver: Standardisation du calendrier officiel des jours fériés et vacances scolaires
WITH base AS (
    SELECT * FROM {{ ref('stg_holidays_lu') }}
)
SELECT
    TRY_CAST(raw_date AS DATE) AS holiday_date,
    holiday_name_fr,
    holiday_name_de,
    holiday_name_lb,
    is_legal_holiday,
    is_school_vacation,
    source_id
FROM base
WHERE raw_date IS NOT NULL
