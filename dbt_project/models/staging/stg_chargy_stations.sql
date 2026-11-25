-- Staging bornes Chargy (état live des connecteurs par site)
{% set cols = {'site_name': 'VARCHAR', 'address': 'VARCHAR', 'connectors_total': 'INTEGER', 'connectors_available': 'INTEGER', 'connectors_charging': 'INTEGER', 'connectors_out_of_service': 'INTEGER', 'max_power_kw': 'DOUBLE', 'lat': 'DOUBLE', 'lon': 'DOUBLE'} %}
SELECT * FROM {{ bronze('chargy_stations', cols) }}
