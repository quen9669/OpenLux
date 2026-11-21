-- Gold: Data Mart final des jours fériés légaux et traditions de la Grande Région (LU, FR, BE, DE, Lorraine)
SELECT
    holiday_date,
    TRY_CAST(holiday_date AS TIMESTAMP) AS observed_at_utc,
    country_code,
    country_name,
    region_code,
    holiday_name_fr AS holiday_name,
    holiday_name_fr,
    holiday_name_de,
    holiday_name_lb,
    is_legal_holiday,
    is_customary_tradition,
    is_school_vacation,
    source_id
FROM {{ ref('silver_holidays') }}
