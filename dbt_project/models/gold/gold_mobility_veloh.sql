-- Gold: Data Mart final des stations vélos en libre-service Vel'oH
SELECT
    station_id,
    station_name,
    observed_at_utc,
    available_bikes,
    available_stands,
    broken_or_disabled_stands,
    total_capacity,
    occupancy_rate,
    is_installed,
    is_renting,
    hourly_rate_eur,
    tariff_details,
    opening_hours,
    lat,
    lon,
    commune_lau,
    canton,
    source_id
FROM {{ ref('silver_mobility_veloh') }}
