{#
  Macros OpenLux V3.
  - bronze(source_id, columns) : lit toutes les archives Bronze d'une source avec un schéma EXPLICITE
    (une source jamais collectée a un fichier '[]' => 0 ligne, jamais de donnée de substitution),
    et ajoute collected_at_utc déduit du nom d'archive (horodatage de collecte réel).
  - with_commune(rel) : rattache chaque point (lat, lon) à la commune dont le centroïde officiel
    est le plus proche (<= 8 km, sinon NULL : point hors Luxembourg).
#}

{% macro bronze(source_id, columns) %}
    (
        SELECT
            * EXCLUDE (filename),
            TRY_STRPTIME(
                REGEXP_EXTRACT(filename, '_(\d{8}T\d{6}Z)_', 1), '%Y%m%dT%H%M%SZ'
            )::TIMESTAMP AS collected_at_utc,
            '{{ source_id }}' AS source_id
        FROM read_json(
            '../data/bronze/{{ source_id }}/**/*.json.gz',
            format = 'array',
            columns = {{ columns }},
            filename = true
        )
    )
{% endmacro %}


{% macro utc(col) %}TRY_CAST({{ col }} AS TIMESTAMPTZ) AT TIME ZONE 'UTC'{% endmacro %}


{% macro with_commune(rel) %}
    WITH _base AS ({{ rel }}),
    _pts AS (
        SELECT DISTINCT lat, lon FROM _base WHERE lat IS NOT NULL AND lon IS NOT NULL
    ),
    _dist AS (
        SELECT
            p.lat, p.lon, c.code_lau, c.commune_name, c.canton,
            -- POURQUOI : approximation équirectangulaire (1° lat = 111,2 km ; 1° lon ≈ 72 km à 49,7° N)
            SQRT(POWER((p.lat - c.lat) * 111.2, 2) + POWER((p.lon - c.lon) * 72.0, 2)) AS d_km
        FROM _pts p CROSS JOIN {{ ref('ref_communes_lu') }} c
    ),
    _near AS (
        SELECT
            lat, lon,
            ARG_MIN(code_lau, d_km) AS commune_lau,
            ARG_MIN(commune_name, d_km) AS commune_name,
            ARG_MIN(canton, d_km) AS canton,
            MIN(d_km) AS d_km
        FROM _dist
        GROUP BY lat, lon
    )
    SELECT
        b.*,
        CASE WHEN n.d_km <= 8 THEN n.commune_lau END AS commune_lau,
        CASE WHEN n.d_km <= 8 THEN n.commune_name END AS commune_name,
        CASE WHEN n.d_km <= 8 THEN n.canton END AS canton
    FROM _base b
    LEFT JOIN _near n ON b.lat = n.lat AND b.lon = n.lon
{% endmacro %}
