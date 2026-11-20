-- Gold: Data Mart final des jours fériés légaux et vacances scolaires au Luxembourg
SELECT
    holiday_date,
    TRY_CAST(holiday_date AS TIMESTAMP) AS observed_at_utc,
    holiday_name_fr,
    holiday_name_de,
    holiday_name_lb,
    is_legal_holiday,
    is_school_vacation,
    NULL::VARCHAR AS commune_lau,
    NULL::DOUBLE AS lat,
    NULL::DOUBLE AS lon,
    source_id
FROM {{ ref('silver_holidays') }}
