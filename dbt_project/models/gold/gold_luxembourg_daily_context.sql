-- Gold: Vue consolidée multimodale quotidienne du Luxembourg (les 8 signaux)
-- Grain: context_date x commune_lau avec complétude garantie et scoring qualité
WITH ref_communes AS (
    SELECT code_lau AS commune_lau, commune_name, canton, lat, lon
    FROM {{ ref('ref_communes_lu') }}
),
distinct_dates AS (
    SELECT DISTINCT CAST(observed_at_utc AS DATE) AS context_date FROM {{ ref('gold_weather_observations') }} WHERE observed_at_utc IS NOT NULL
    UNION
    SELECT DISTINCT CAST(observed_at_utc AS DATE) AS context_date FROM {{ ref('gold_traffic_events') }} WHERE observed_at_utc IS NOT NULL
    UNION
    SELECT DISTINCT CAST(observed_at_utc AS DATE) AS context_date FROM {{ ref('gold_air_quality') }} WHERE observed_at_utc IS NOT NULL
),
dates_communes AS (
    SELECT d.context_date, c.commune_lau, c.commune_name, c.canton, c.lat, c.lon
    FROM distinct_dates d
    CROSS JOIN ref_communes c
),
-- 1. Météo locale et fallback national
weather_daily AS (
    SELECT
        CAST(observed_at_utc AS DATE) AS context_date,
        commune_lau,
        ROUND(AVG(temperature), 1) AS avg_temperature_c,
        ROUND(SUM(precipitation_mm), 1) AS total_precipitation_mm,
        ROUND(MAX(wind_speed_kmh), 1) AS max_wind_speed_kmh
    FROM {{ ref('gold_weather_observations') }}
    WHERE commune_lau IS NOT NULL
    GROUP BY 1, 2
),
weather_national AS (
    SELECT
        CAST(observed_at_utc AS DATE) AS context_date,
        ROUND(AVG(temperature), 1) AS avg_temperature_c,
        ROUND(SUM(precipitation_mm), 1) AS total_precipitation_mm,
        ROUND(MAX(wind_speed_kmh), 1) AS max_wind_speed_kmh
    FROM {{ ref('gold_weather_observations') }}
    GROUP BY 1
),
-- 2. Qualité de l'air locale et fallback national
air_quality_daily AS (
    SELECT
        CAST(observed_at_utc AS DATE) AS context_date,
        commune_lau,
        MAX(aqi_index) AS max_aqi_index
    FROM {{ ref('gold_air_quality') }}
    WHERE commune_lau IS NOT NULL
    GROUP BY 1, 2
),
air_quality_national AS (
    SELECT
        CAST(observed_at_utc AS DATE) AS context_date,
        MAX(aqi_index) AS max_aqi_index
    FROM {{ ref('gold_air_quality') }}
    GROUP BY 1
),
-- 3. Jours fériés & Vacances scolaires
holidays_daily AS (
    SELECT
        CAST(holiday_date AS DATE) AS context_date,
        BOOL_OR(is_legal_holiday) AS is_legal_holiday,
        BOOL_OR(is_school_vacation) AS is_school_vacation,
        MAX(holiday_name_fr) AS holiday_name
    FROM {{ ref('gold_holidays') }}
    GROUP BY 1
),
-- 4. Trafic routier & frontalier
traffic_daily AS (
    SELECT
        context_date,
        commune_lau,
        COUNT(*) AS traffic_events_count
    FROM (
        SELECT CAST(observed_at_utc AS DATE) AS context_date, commune_lau FROM {{ ref('gold_traffic_events') }}
        UNION ALL
        SELECT CAST(observed_at_utc AS DATE) AS context_date, commune_lau FROM {{ ref('gold_crossborder_traffic') }}
    ) t
    GROUP BY 1, 2
),
-- 5. Chantiers actifs
roadworks_daily AS (
    SELECT
        d.context_date,
        r.commune_lau,
        COUNT(*) AS active_roadworks_count
    FROM distinct_dates d
    JOIN {{ ref('gold_roadworks') }} r
        ON d.context_date >= CAST(r.start_date AS DATE)
        AND d.context_date <= CAST(r.end_date AS DATE)
    GROUP BY 1, 2
),
-- 6. Grèves & Perturbations
strikes_daily AS (
    SELECT
        CAST(published_at_utc AS DATE) AS context_date,
        commune_lau,
        COUNT(*) AS strikes_count
    FROM {{ ref('gold_strikes_disruptions') }}
    GROUP BY 1, 2
),
-- 7. Niveaux d'eau et crues (local et national)
water_daily AS (
    SELECT
        CAST(observed_at_utc AS DATE) AS context_date,
        commune_lau,
        MAX(alert_level) AS max_water_alert_status
    FROM {{ ref('gold_water_levels') }}
    WHERE commune_lau IS NOT NULL
    GROUP BY 1, 2
),
water_national AS (
    SELECT
        CAST(observed_at_utc AS DATE) AS context_date,
        MAX(alert_level) AS max_water_alert_status
    FROM {{ ref('gold_water_levels') }}
    GROUP BY 1
),
-- 8. Événements majeurs et manifestations
events_daily AS (
    SELECT
        d.context_date,
        e.commune_lau,
        COUNT(*) AS major_events_count
    FROM distinct_dates d
    JOIN {{ ref('gold_culture_events') }} e
        ON d.context_date >= CAST(e.start_date AS DATE)
        AND d.context_date <= COALESCE(CAST(e.end_date AS DATE), CAST(e.start_date AS DATE))
    GROUP BY 1, 2
),
consolidated AS (
    SELECT
        dc.context_date,
        dc.commune_lau,
        dc.commune_name,
        dc.canton,
        dc.lat,
        dc.lon,
        -- 1. Météo (locale prioritaire, sinon moyenne nationale Grand-Duché)
        COALESCE(w.avg_temperature_c, wn.avg_temperature_c) AS avg_temperature_c,
        COALESCE(w.total_precipitation_mm, wn.total_precipitation_mm, 0.0) AS total_precipitation_mm,
        COALESCE(w.max_wind_speed_kmh, wn.max_wind_speed_kmh) AS max_wind_speed_kmh,
        (w.avg_temperature_c IS NULL AND wn.avg_temperature_c IS NOT NULL) AS is_weather_interpolated,
        -- 2. Qualité de l'air (locale prioritaire, sinon pic national)
        COALESCE(aq.max_aqi_index, aqn.max_aqi_index) AS max_aqi_index,
        -- 3. Jours fériés & Vacances
        COALESCE(h.is_legal_holiday, FALSE) AS is_legal_holiday,
        COALESCE(h.is_school_vacation, FALSE) AS is_school_vacation,
        h.holiday_name,
        -- 4. Trafic routier & frontalier
        COALESCE(tr.traffic_events_count, 0) AS traffic_events_count,
        -- 5. Chantiers actifs
        COALESCE(rw.active_roadworks_count, 0) AS active_roadworks_count,
        -- 6. Grèves & Perturbations
        COALESCE(st.strikes_count, 0) AS strikes_count,
        -- 7. Niveaux d'eau
        COALESCE(wl.max_water_alert_status, wln.max_water_alert_status, 'NORMAL') AS max_water_alert_status,
        -- 8. Événements & Sorties
        COALESCE(ev.major_events_count, 0) AS major_events_count,
        'openlux_consolidated' AS source_id
    FROM dates_communes dc
    LEFT JOIN weather_daily w ON dc.context_date = w.context_date AND dc.commune_lau = w.commune_lau
    LEFT JOIN weather_national wn ON dc.context_date = wn.context_date
    LEFT JOIN air_quality_daily aq ON dc.context_date = aq.context_date AND dc.commune_lau = aq.commune_lau
    LEFT JOIN air_quality_national aqn ON dc.context_date = aqn.context_date
    LEFT JOIN holidays_daily h ON dc.context_date = h.context_date
    LEFT JOIN traffic_daily tr ON dc.context_date = tr.context_date AND dc.commune_lau = tr.commune_lau
    LEFT JOIN roadworks_daily rw ON dc.context_date = rw.context_date AND dc.commune_lau = rw.commune_lau
    LEFT JOIN strikes_daily st ON dc.context_date = st.context_date AND dc.commune_lau = st.commune_lau
    LEFT JOIN water_daily wl ON dc.context_date = wl.context_date AND dc.commune_lau = wl.commune_lau
    LEFT JOIN water_national wln ON dc.context_date = wln.context_date
    LEFT JOIN events_daily ev ON dc.context_date = ev.context_date AND dc.commune_lau = ev.commune_lau
)
SELECT
    context_date,
    commune_lau,
    commune_name,
    canton,
    lat,
    lon,
    avg_temperature_c,
    total_precipitation_mm,
    max_wind_speed_kmh,
    max_aqi_index,
    is_legal_holiday,
    is_school_vacation,
    holiday_name,
    traffic_events_count,
    active_roadworks_count,
    strikes_count,
    max_water_alert_status,
    major_events_count,
    -- Score de complétude calculé sur les 8 signaux
    ROUND(
        (
            CASE WHEN avg_temperature_c IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN max_aqi_index IS NOT NULL THEN 1 ELSE 0 END +
            1 + -- Calendrier légal toujours résolu
            1 + -- Trafic (0 ou >0)
            1 + -- Chantiers (0 ou >0)
            1 + -- Grèves (0 ou >0)
            CASE WHEN max_water_alert_status IS NOT NULL THEN 1 ELSE 0 END +
            1   -- Événements (0 ou >0)
        ) * 100.0 / 8.0,
        1
    ) AS data_completeness_pct,
    CASE
        WHEN NOT is_weather_interpolated AND avg_temperature_c IS NOT NULL AND max_aqi_index IS NOT NULL THEN 'EXCELLENT'
        WHEN is_weather_interpolated AND avg_temperature_c IS NOT NULL THEN 'GOOD'
        ELSE 'PARTIAL'
    END AS data_quality_grade,
    is_weather_interpolated AS is_interpolated,
    source_id
FROM consolidated
