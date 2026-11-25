-- Gold chantiers (Ponts et Chaussées + Ville de Luxembourg) : dernier état de chaque chantier
{{ with_commune("SELECT * EXCLUDE (start_time_utc, end_time_utc), " ~ utc('start_time_utc') ~ " AS start_time_utc, " ~ utc('end_time_utc') ~ " AS end_time_utc FROM " ~ ref('stg_roadworks')) }}
QUALIFY ROW_NUMBER() OVER (PARTITION BY source_id, work_id ORDER BY collected_at_utc DESC) = 1
