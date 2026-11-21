-- Gold: Vue consolidée multimodale quotidienne du Luxembourg (les 8 signaux)
-- Grain: date x commune_lau
WITH ref_communes AS (
    SELECT code_lau AS commune_lau, commune_name, canton, lat, lon
    FROM {{ ref('ref_communes_lu') }}
),
distinct_dates AS (
    SELECT DISTINCT CAST(observed_at_utc AS DATE) AS context_date FROM {{ ref('gold_weather_observations') }} WHERE observed_at_utc IS NOT NULL
    UNION
    SELECT DISTINCT CAST(holiday_date AS DATE) AS context_date FROM {{ ref('gold_holidays') }} WHERE holiday_date IS NOT NULL
    UNION
    SELECT DISTINCT CAST(observed_at_utc AS DATE) AS context_date FROM {{ ref('gold_traffic_events') }} WHERE observed_at_utc IS NOT NULL
),
dates_communes AS (
    SELECT d.context_date, c.commune_lau, c.commune_name, c.canton, c.lat, c.lon
    FROM distinct_dates d
    CROSS JOIN ref_communes c
),
weather_daily AS (
    SELECT
        CAST(observed_at_utc AS DATE) AS context_date,
        commune_lau,
        ROUND(AVG(temperature), 1) AS avg_temperature_c,
        ROUND(SUM(precipitation_mm), 1) AS total_precipitation_mm,
        ROUND(MAX(wind_speed_kmh), 1) AS max_wind_speed_kmh
    FROM {{ ref('gold_weather_observations') }}
    GROUP BY 1, 2
),
air_quality_daily AS (
    SELECT
        CAST(observed_at_utc AS DATE) AS context_date,
        commune_lau,
        MAX(aqi_index) AS max_aqi_index
    FROM {{ ref('gold_air_quality') }}
    GROUP BY 1, 2
),
holidays_daily AS (
    SELECT
        CAST(holiday_date AS DATE) AS context_date,
        BOOL_OR(is_legal_holiday) AS is_legal_holiday,
        BOOL_OR(is_school_vacation) AS is_school_vacation
    FROM {{ ref('gold_holidays') }}
    GROUP BY 1
),
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
strikes_daily AS (
    SELECT
        CAST(published_at_utc AS DATE) AS context_date,
        commune_lau,
        COUNT(*) AS strikes_count
    FROM {{ ref('gold_strikes_disruptions') }}
    GROUP BY 1, 2
),
water_daily AS (
    SELECT
        CAST(observed_at_utc AS DATE) AS context_date,
        commune_lau,
        MAX(alert_level) AS max_water_alert_status
    FROM {{ ref('gold_water_levels') }}
    GROUP BY 1, 2
),
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
)
SELECT
    dc.context_date,
    dc.commune_lau,
    dc.commune_name,
    dc.canton,
    dc.lat,
    dc.lon,
    -- 1. Météo
    w.avg_temperature_c,
    w.total_precipitation_mm,
    w.max_wind_speed_kmh,
    -- 2. Qualité de l'air
    aq.max_aqi_index,
    -- 3. Jours fériés & Vacances
    COALESCE(h.is_legal_holiday, FALSE) AS is_legal_holiday,
    COALESCE(h.is_school_vacation, FALSE) AS is_school_vacation,
    -- 4. Trafic routier & frontalier
    COALESCE(tr.traffic_events_count, 0) AS traffic_events_count,
    -- 5. Chantiers actifs
    COALESCE(rw.active_roadworks_count, 0) AS active_roadworks_count,
    -- 6. Grèves & Perturbations
    COALESCE(st.strikes_count, 0) AS strikes_count,
    -- 7. Niveaux d'eau
    wl.max_water_alert_status,
    -- 8. Événements & Sorties
    COALESCE(ev.major_events_count, 0) AS major_events_count,
    'openlux_consolidated' AS source_id
FROM dates_communes dc
LEFT JOIN weather_daily w ON dc.context_date = w.context_date AND dc.commune_lau = w.commune_lau
LEFT JOIN air_quality_daily aq ON dc.context_date = aq.context_date AND dc.commune_lau = aq.commune_lau
LEFT JOIN holidays_daily h ON dc.context_date = h.context_date
LEFT JOIN traffic_daily tr ON dc.context_date = tr.context_date AND dc.commune_lau = tr.commune_lau
LEFT JOIN roadworks_daily rw ON dc.context_date = rw.context_date AND dc.commune_lau = rw.commune_lau
LEFT JOIN strikes_daily st ON dc.context_date = st.context_date AND dc.commune_lau = st.commune_lau
LEFT JOIN water_daily wl ON dc.context_date = wl.context_date AND dc.commune_lau = wl.commune_lau
LEFT JOIN events_daily ev ON dc.context_date = ev.context_date AND dc.commune_lau = ev.commune_lau
WHERE w.avg_temperature_c IS NOT NULL
   OR aq.max_aqi_index IS NOT NULL
   OR h.is_legal_holiday = TRUE
   OR tr.traffic_events_count > 0
   OR rw.active_roadworks_count > 0
   OR st.strikes_count > 0
   OR wl.max_water_alert_status IS NOT NULL
   OR ev.major_events_count > 0
