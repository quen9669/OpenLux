-- Gold équipements publics : recyclage, défibrillateurs (OSM), itinéraires cyclables
{{ with_commune("SELECT * FROM " ~ ref('stg_equipment')) }}
-- POURQUOI : la requête OSM est une bbox ; on écarte les points sans commune LU à <= 8 km
WHERE source_id <> 'aed_osm' OR n.d_km <= 8
QUALIFY ROW_NUMBER() OVER (PARTITION BY source_id, item_id ORDER BY collected_at_utc DESC) = 1
