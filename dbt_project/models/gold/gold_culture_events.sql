-- Gold agenda culturel (echo.lu, Ville de Luxembourg, Rockhal) — champs factuels uniquement
{{ with_commune("SELECT * EXCLUDE (start_utc, end_utc), " ~ utc('start_utc') ~ " AS start_utc, " ~ utc('end_utc') ~ " AS end_utc FROM " ~ ref('stg_culture_events')) }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY collected_at_utc DESC) = 1
