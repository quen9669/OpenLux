-- Gold: Data Mart final des mobilités douces, parkings et bornes de recharge
SELECT
    facility_id,
    facility_type,
    facility_name,
    observed_at_utc,
    available_capacity,
    total_capacity,
    occupancy_rate,
    opening_hours,
    hourly_rate_eur,
    tariff_details,
    is_free_pr,
    lat,
    lon,
    commune_lau,
    canton,
    source_id
FROM {{ ref('silver_mobility_parkings') }}
