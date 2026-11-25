-- Staging équipements : centres de recyclage, défibrillateurs (OSM), itinéraires cyclables
{% set poi = {'item_id': 'VARCHAR', 'category': 'VARCHAR', 'name': 'VARCHAR', 'details': 'VARCHAR', 'lat': 'DOUBLE', 'lon': 'DOUBLE'} %}
{% set bike = {'route_id': 'VARCHAR', 'route_name': 'VARCHAR', 'length_km': 'DOUBLE', 'lat': 'DOUBLE', 'lon': 'DOUBLE'} %}
SELECT *, NULL::DOUBLE AS length_km FROM {{ bronze('recycling_centers', poi) }}
UNION ALL BY NAME
SELECT *, NULL::DOUBLE AS length_km FROM {{ bronze('aed_osm', poi) }}
UNION ALL BY NAME
SELECT
    route_id AS item_id, 'cycle_route' AS category, route_name AS name, NULL::VARCHAR AS details,
    length_km, lat, lon, collected_at_utc, source_id
FROM {{ bronze('bike_routes_regional', bike) }}
