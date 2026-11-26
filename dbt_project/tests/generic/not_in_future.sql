-- Test générique : aucune valeur de la colonne postérieure à maintenant (+ tolérance), 0 ligne attendue
{% test not_in_future(model, column_name, tolerance_hours=1) %}
SELECT {{ column_name }}
FROM {{ model }}
WHERE CAST({{ column_name }} AS TIMESTAMP)
    > CAST(current_timestamp AT TIME ZONE 'UTC' AS TIMESTAMP) + INTERVAL {{ tolerance_hours }} HOUR
{% endtest %}
