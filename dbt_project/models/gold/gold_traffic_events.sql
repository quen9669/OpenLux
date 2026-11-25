-- Gold événements trafic LU + frontaliers : dernier état connu de chaque événement
{{ with_commune("SELECT * EXCLUDE (observed_at, start_time_utc, end_time_utc), " ~ utc('start_time_utc') ~ " AS start_time_utc, " ~ utc('end_time_utc') ~ " AS end_time_utc, " ~ utc('observed_at') ~ " AS record_version_utc, MIN(collected_at_utc) OVER (PARTITION BY source_id, event_id) AS first_seen_utc FROM " ~ ref('stg_traffic_events')) }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY source_id, event_id ORDER BY collected_at_utc DESC) = 1
