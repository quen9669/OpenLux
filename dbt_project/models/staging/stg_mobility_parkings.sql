-- Staging parkings temps réel de la Ville de Luxembourg
{% set cols = {'parking_id': 'VARCHAR', 'parking_name': 'VARCHAR', 'observed_at': 'VARCHAR', 'available_spaces': 'INTEGER', 'total_capacity': 'INTEGER', 'trend': 'INTEGER', 'is_open': 'BOOLEAN', 'is_full': 'BOOLEAN', 'is_out_of_order': 'BOOLEAN', 'pricing_policy': 'VARCHAR', 'district': 'VARCHAR', 'lat': 'DOUBLE', 'lon': 'DOUBLE'} %}
SELECT * FROM {{ bronze('parkings_vdl', cols) }}
