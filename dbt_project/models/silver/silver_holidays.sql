-- Silver: Standardisation du calendrier officiel des jours fériés et traditions (Grande Région)
WITH lu_holidays AS (
    SELECT
        TRY_CAST(raw_date AS DATE) AS holiday_date,
        'LU' AS country_code,
        'Luxembourg' AS country_name,
        'NATIONAL' AS region_code,
        holiday_name_fr,
        holiday_name_de,
        holiday_name_lb,
        is_legal_holiday,
        false AS is_customary_tradition,
        is_school_vacation,
        source_id
    FROM {{ ref('stg_holidays_lu') }}
    WHERE raw_date IS NOT NULL
      AND TRY_CAST(raw_date AS DATE) IS NOT NULL
),
crossborder AS (
    SELECT
        TRY_CAST(holiday_date AS DATE) AS holiday_date,
        country_code,
        country_name,
        region_code,
        holiday_name_fr,
        holiday_name_de,
        holiday_name_lb,
        is_legal_holiday,
        is_customary_tradition,
        is_school_vacation,
        'ref_crossborder_holidays' AS source_id
    FROM {{ ref('ref_crossborder_holidays') }}
    WHERE holiday_date IS NOT NULL
      AND TRY_CAST(holiday_date AS DATE) IS NOT NULL
),
combined AS (
    SELECT * FROM lu_holidays
    UNION ALL
    SELECT * FROM crossborder
),
deduped AS (
    SELECT
        holiday_date,
        country_code,
        country_name,
        region_code,
        holiday_name_fr,
        holiday_name_de,
        holiday_name_lb,
        is_legal_holiday,
        is_customary_tradition,
        is_school_vacation,
        source_id,
        ROW_NUMBER() OVER (
            PARTITION BY holiday_date, country_code, region_code, holiday_name_fr
            ORDER BY CASE WHEN source_id = 'holidays_lu' THEN 1 ELSE 2 END
        ) AS rn
    FROM combined
    WHERE holiday_date IS NOT NULL
)
SELECT
    holiday_date,
    country_code,
    country_name,
    region_code,
    holiday_name_fr,
    holiday_name_de,
    holiday_name_lb,
    is_legal_holiday,
    is_customary_tradition,
    is_school_vacation,
    source_id
FROM deduped
WHERE rn = 1
