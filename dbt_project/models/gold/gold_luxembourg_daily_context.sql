-- Gold contexte quotidien par canton : météo (modèle), air, calendrier, trafic, chantiers.
-- POURQUOI : une ligne = (jour, canton) ; aucune valeur imputée, NULL si la source est absente.
WITH wx AS (
    SELECT
        CAST(observed_at_utc AS DATE) AS context_date, canton,
        ROUND(AVG(temperature_c), 1) AS avg_temperature_c,
        MIN(temperature_c) AS min_temperature_c,
        MAX(temperature_c) AS max_temperature_c,
        ROUND(SUM(precipitation_mm), 1) AS total_precipitation_mm,
        MAX(wind_speed_kmh) AS max_wind_speed_kmh
    FROM {{ ref('gold_weather_observations') }}
    WHERE data_origin = 'model' AND canton IS NOT NULL
    GROUP BY ALL
),
aq AS (
    SELECT CAST(observed_at_utc AS DATE) AS context_date, canton, MAX(value) AS max_european_aqi
    FROM {{ ref('gold_air_quality') }}
    WHERE pollutant = 'european_aqi' AND canton IS NOT NULL
    GROUP BY ALL
),
pub AS (
    SELECT holiday_date AS context_date, ANY_VALUE(name_fr) AS holiday_name
    FROM {{ ref('gold_holidays') }}
    WHERE country_code = 'LU' AND holiday_type = 'public'
    GROUP BY ALL
),
school AS (
    SELECT holiday_date, end_date, name_fr FROM {{ ref('gold_holidays') }}
    WHERE country_code = 'LU' AND holiday_type = 'school'
),
trf AS (
    SELECT CAST(first_seen_utc AS DATE) AS context_date, canton, COUNT(*) AS new_traffic_events
    FROM {{ ref('gold_traffic_events') }}
    WHERE country_code = 'LU' AND canton IS NOT NULL
    GROUP BY ALL
),
rw AS (
    SELECT canton, CAST(start_time_utc AS DATE) AS d0, CAST(end_time_utc AS DATE) AS d1
    FROM {{ ref('gold_roadworks') }}
    WHERE canton IS NOT NULL AND start_time_utc IS NOT NULL
)
SELECT
    wx.context_date,
    wx.canton,
    wx.avg_temperature_c,
    wx.min_temperature_c,
    wx.max_temperature_c,
    wx.total_precipitation_mm,
    wx.max_wind_speed_kmh,
    aq.max_european_aqi,
    pub.holiday_name IS NOT NULL AS is_public_holiday,
    pub.holiday_name,
    EXISTS (
        SELECT 1 FROM school s WHERE wx.context_date BETWEEN s.holiday_date AND s.end_date
    ) AS is_school_holiday,
    COALESCE(trf.new_traffic_events, 0) AS new_traffic_events,
    (
        SELECT COUNT(*) FROM rw
        WHERE rw.canton = wx.canton AND wx.context_date BETWEEN rw.d0 AND COALESCE(rw.d1, wx.context_date)
    ) AS active_roadworks,
    CURRENT_TIMESTAMP AT TIME ZONE 'UTC' AS computed_at_utc
FROM wx
LEFT JOIN aq USING (context_date, canton)
LEFT JOIN pub USING (context_date)
LEFT JOIN trf USING (context_date, canton)
