-- Gold: Data Mart final des parkings publics et P+R
SELECT
    parking_id,
    parking_name,
    observed_at_utc,
    available_spaces,
    total_capacity,
    occupied_spaces,
    occupancy_rate,
    trend,
    is_open,
    is_full,
    is_out_of_order,
    is_free_pr,
    hourly_rate_eur,
    tariff_details,
    opening_hours,
    lat,
    lon,
    commune_lau,
    canton,
    source_id
FROM {{ ref('silver_mobility_parkings') }}
