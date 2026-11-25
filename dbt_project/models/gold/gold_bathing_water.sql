-- Gold eaux de baignade : statut courant + classe de qualité par site (dernier état)
{% set rel %}
SELECT s.site_id, s.site_name, s.bathing_status, q.quality_class, s.profile_url, s.lat, s.lon, s.collected_at_utc, s.source_id
FROM (
    SELECT * FROM {{ ref('stg_bathing_water') }} WHERE source_id = 'bathing_status_age'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY site_id ORDER BY collected_at_utc DESC) = 1
) s
LEFT JOIN (
    SELECT site_id, quality_class FROM {{ ref('stg_bathing_water') }} WHERE source_id = 'bathing_quality_age'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY site_id ORDER BY collected_at_utc DESC) = 1
) q USING (site_id)
{% endset %}
{{ with_commune(rel) }}
