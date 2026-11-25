-- Chaque table Gold respecte sa clé métier (GOLD_KEYS, core/gold.py) : 0 ligne attendue
SELECT 'gold_weather_observations' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_weather_observations') }} GROUP BY station_id, observed_at_utc HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_air_quality' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_air_quality') }} GROUP BY station_id, observed_at_utc, pollutant HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_water_levels' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_water_levels') }} GROUP BY station_name, observed_at_utc HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_bathing_water' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_bathing_water') }} GROUP BY site_id HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_traffic_events' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_traffic_events') }} GROUP BY source_id, event_id HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_roadworks' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_roadworks') }} GROUP BY source_id, work_id HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_transit_disruptions' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_transit_disruptions') }} GROUP BY source_id, disruption_id HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_mobility_veloh' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_mobility_veloh') }} GROUP BY station_number, observed_at_utc HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_mobility_parkings' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_mobility_parkings') }} GROUP BY parking_id, observed_at_utc HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_chargy_stations' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_chargy_stations') }} GROUP BY site_name, collected_at_utc HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_aviation' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_aviation') }} GROUP BY icao24, observed_at_utc HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_fuel_prices' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_fuel_prices') }} GROUP BY reference_month, energy_type HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_inflation' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_inflation') }} GROUP BY reference_month HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_electricity_spot' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_electricity_spot') }} GROUP BY observed_at_utc HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_building_permits' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_building_permits') }} GROUP BY canton_code, building_type_code, reference_year HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_housing_prices' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_housing_prices') }} GROUP BY reference_year, property_type, commune_name HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_unemployment' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_unemployment') }} GROUP BY reference_month, commune_name, sex HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_holidays' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_holidays') }} GROUP BY holiday_date, country_code, region_code, holiday_type HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_weather_warnings' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_weather_warnings') }} GROUP BY alert_id, area HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_equipment' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_equipment') }} GROUP BY source_id, item_id HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_petitions' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_petitions') }} GROUP BY petition_id HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_culture_events' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_culture_events') }} GROUP BY event_id HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_strikes_news' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_strikes_news') }} GROUP BY article_id HAVING COUNT(*) > 1
UNION ALL
SELECT 'gold_luxembourg_daily_context' AS gold_table, COUNT(*) AS n FROM {{ ref('gold_luxembourg_daily_context') }} GROUP BY context_date, canton HAVING COUNT(*) > 1
