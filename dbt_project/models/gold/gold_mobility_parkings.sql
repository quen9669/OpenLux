-- Gold parkings Ville de Luxembourg : série temporelle de l'occupation
{{ with_commune("SELECT * EXCLUDE (observed_at), " ~ utc('observed_at') ~ " AS observed_at_utc, CASE WHEN total_capacity > 0 THEN ROUND(100.0 * (total_capacity - available_spaces) / total_capacity, 1) END AS occupancy_pct FROM " ~ ref('stg_mobility_parkings')) }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY parking_id, observed_at_utc ORDER BY collected_at_utc DESC) = 1
