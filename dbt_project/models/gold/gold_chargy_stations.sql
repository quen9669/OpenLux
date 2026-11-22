-- Gold: Data Mart final des bornes de recharge électrique Chargy
SELECT
    station_id,
    station_name,
    network_operator,
    observed_at_utc,
    available_charging_points,
    total_charging_points,
    occupied_charging_points,
    occupancy_rate,
    power_kw,
    connector_types,
    tariff_details,
    opening_hours,
    lat,
    lon,
    commune_lau,
    canton,
    source_id
FROM {{ ref('silver_chargy_stations') }}
