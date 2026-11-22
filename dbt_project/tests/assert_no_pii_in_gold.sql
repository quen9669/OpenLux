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

    UNION ALL

    SELECT
        'gold_crossborder_traffic' AS table_name,
        comment AS sampled_text
    FROM {{ ref('gold_crossborder_traffic') }}
    WHERE comment IS NOT NULL AND (
        regexp_matches(comment, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
        OR regexp_matches(comment, '(?:\+352|00352)\s?[0-9]{4,}')
    )

    UNION ALL

    SELECT
        'gold_public_transit' AS table_name,
        message AS sampled_text
    FROM {{ ref('gold_public_transit') }}
    WHERE message IS NOT NULL AND (
        regexp_matches(message, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
        OR regexp_matches(message, '(?:\+352|00352)\s?[0-9]{4,}')
    )

    UNION ALL

    SELECT
        'gold_mobility_parkings' AS table_name,
        parking_name AS sampled_text
    FROM {{ ref('gold_mobility_parkings') }}
    WHERE regexp_matches(parking_name, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
       OR regexp_matches(parking_name, '(?:\+352|00352)\s?[0-9]{4,}')

    UNION ALL

    SELECT
        'gold_mobility_veloh' AS table_name,
        station_name AS sampled_text
    FROM {{ ref('gold_mobility_veloh') }}
    WHERE regexp_matches(station_name, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
       OR regexp_matches(station_name, '(?:\+352|00352)\s?[0-9]{4,}')

    UNION ALL

    SELECT
        'gold_chargy_stations' AS table_name,
        station_name AS sampled_text
    FROM {{ ref('gold_chargy_stations') }}
    WHERE regexp_matches(station_name, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
       OR regexp_matches(station_name, '(?:\+352|00352)\s?[0-9]{4,}')

    UNION ALL

    SELECT
        'gold_aviation_noise' AS table_name,
        callsign_or_zone AS sampled_text
    FROM {{ ref('gold_aviation_noise') }}
    WHERE regexp_matches(callsign_or_zone, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
       OR regexp_matches(callsign_or_zone, '(?:\+352|00352)\s?[0-9]{4,}')

    UNION ALL

    SELECT
        'gold_roadworks' AS table_name,
        title AS sampled_text
    FROM {{ ref('gold_roadworks') }}
    WHERE title IS NOT NULL AND (
        regexp_matches(title, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
        OR regexp_matches(title, '(?:\+352|00352)\s?[0-9]{4,}')
    )

    UNION ALL

    SELECT
        'gold_housing' AS table_name,
        COALESCE(description, property_type) AS sampled_text
    FROM {{ ref('gold_housing') }}
    WHERE (description IS NOT NULL AND (
        regexp_matches(description, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
        OR regexp_matches(description, '(?:\+352|00352)\s?[0-9]{4,}')
    )) OR (
        regexp_matches(property_type, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
        OR regexp_matches(property_type, '(?:\+352|00352)\s?[0-9]{4,}')
    )

    UNION ALL

    SELECT
        'gold_housing_listings' AS table_name,
        COALESCE(description, property_type) AS sampled_text
    FROM {{ ref('gold_housing_listings') }}
    WHERE (description IS NOT NULL AND (
        regexp_matches(description, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
        OR regexp_matches(description, '(?:\+352|00352)\s?[0-9]{4,}')
    )) OR (
        regexp_matches(property_type, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
        OR regexp_matches(property_type, '(?:\+352|00352)\s?[0-9]{4,}')
    )

    UNION ALL

    SELECT
        'gold_housing_stats' AS table_name,
        COALESCE(description, property_type) AS sampled_text
    FROM {{ ref('gold_housing_stats') }}
    WHERE (description IS NOT NULL AND (
        regexp_matches(description, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
        OR regexp_matches(description, '(?:\+352|00352)\s?[0-9]{4,}')
    )) OR (
        regexp_matches(property_type, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
        OR regexp_matches(property_type, '(?:\+352|00352)\s?[0-9]{4,}')
    )

    UNION ALL

    SELECT
        'gold_daily_life' AS table_name,
        name AS sampled_text
    FROM {{ ref('gold_daily_life') }}
    WHERE regexp_matches(name, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
       OR regexp_matches(name, '(?:\+352|00352)\s?[0-9]{4,}')

    UNION ALL

    SELECT
        'gold_culture_events' AS table_name,
        title AS sampled_text
    FROM {{ ref('gold_culture_events') }}
    WHERE regexp_matches(title, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
       OR regexp_matches(title, '(?:\+352|00352)\s?[0-9]{4,}')

    UNION ALL

    SELECT
        'gold_strikes_disruptions' AS table_name,
        title AS sampled_text
    FROM {{ ref('gold_strikes_disruptions') }}
    WHERE regexp_matches(title, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
       OR regexp_matches(title, '(?:\+352|00352)\s?[0-9]{4,}')

    UNION ALL

    SELECT
        'gold_health_alerts' AS table_name,
        headline_or_name AS sampled_text
    FROM {{ ref('gold_health_alerts') }}
    WHERE regexp_matches(headline_or_name, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
       OR regexp_matches(headline_or_name, '(?:\+352|00352)\s?[0-9]{4,}')

    UNION ALL

    SELECT
        'gold_civic_life' AS table_name,
        title_or_indicator AS sampled_text
    FROM {{ ref('gold_civic_life') }}
    WHERE regexp_matches(title_or_indicator, '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+')
       OR regexp_matches(title_or_indicator, '(?:\+352|00352)\s?[0-9]{4,}')
)
SELECT * FROM pii_checks
