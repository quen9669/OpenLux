-- Test d'intégrité RGPD : Détection de PII (emails et téléphones) dans les tables Gold
-- Ce test renvoie toute ligne violant la règle Zero-PII. Zéro ligne retournée = Test validé.

WITH pii_checks AS (
    SELECT
        'gold_weather_observations' AS table_name,
        station_name AS sampled_text
    FROM {{ ref('gold_weather_observations') }}
    WHERE regexp_matches(station_name, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
       OR regexp_matches(station_name, '(?:\+352|00352)\s?[0-9]{4,}')

    UNION ALL

    SELECT
        'gold_traffic_events' AS table_name,
        traffic_comment AS sampled_text
    FROM {{ ref('gold_traffic_events') }}
    WHERE traffic_comment IS NOT NULL AND (
        regexp_matches(traffic_comment, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
        OR regexp_matches(traffic_comment, '(?:\+352|00352)\s?[0-9]{4,}')
    )

    UNION ALL

    SELECT
        'gold_holidays' AS table_name,
        holiday_name_fr AS sampled_text
    FROM {{ ref('gold_holidays') }}
    WHERE regexp_matches(holiday_name_fr, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
       OR regexp_matches(holiday_name_fr, '(?:\+352|00352)\s?[0-9]{4,}')

    UNION ALL

    SELECT
        'gold_air_quality' AS table_name,
        station_name AS sampled_text
    FROM {{ ref('gold_air_quality') }}
    WHERE regexp_matches(station_name, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
       OR regexp_matches(station_name, '(?:\+352|00352)\s?[0-9]{4,}')

    UNION ALL

    SELECT
        'gold_water_levels' AS table_name,
        station_name AS sampled_text
    FROM {{ ref('gold_water_levels') }}
    WHERE regexp_matches(station_name, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
       OR regexp_matches(station_name, '(?:\+352|00352)\s?[0-9]{4,}')

    UNION ALL

    SELECT
        'gold_radioactivity' AS table_name,
        station_name AS sampled_text
    FROM {{ ref('gold_radioactivity') }}
    WHERE regexp_matches(station_name, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
       OR regexp_matches(station_name, '(?:\+352|00352)\s?[0-9]{4,}')

    UNION ALL

    SELECT
        'gold_bathing_water' AS table_name,
        site_name AS sampled_text
    FROM {{ ref('gold_bathing_water') }}
    WHERE regexp_matches(site_name, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
       OR regexp_matches(site_name, '(?:\+352|00352)\s?[0-9]{4,}')
)
SELECT * FROM pii_checks
