# Catalogue des données OpenLux (V3)

> Instantané mesuré le 25/11/2026 à partir de `data/gold/*.parquet` (volumes, couverture, sources).
> La version vivante est servie par `GET /v1/datasets` et par le site `/v2/`. Aucune donnée n'est saisie à la main.

| Table | Domaine | Lignes | Couverture | Sources | Licences |
| :--- | :--- | ---: | :--- | :--- | :--- |
| `gold_weather_observations` | Environnement | 22,179 | 2026-09-10 → 2026-11-25 | `meteo_cantons_openmeteo`, `meteo_findel_meteolux` | CC-BY-4.0, CC0-1.0 |
| `gold_air_quality` | Environnement | 267,840 | 2026-08-25 → 2026-11-25 | `air_quality_openmeteo`, `pollen_openmeteo` | CC-BY-4.0 |
| `gold_water_levels` | Environnement | 28,289 | 2026-11-18 → 2026-11-25 | `water_levels_age` | CC0-1.0 |
| `gold_bathing_water` | Environnement | 15 | 2026-11-25 → 2026-11-25 | `bathing_status_age` | CC0-1.0 |
| `gold_weather_warnings` | Environnement | 6 | 2026-11-25 → 2026-11-25 | `weather_warnings_meteoalarm` | CC-BY-4.0 |
| `gold_traffic_events` | Mobilité | 63 | 2023-03-24 → 2026-11-29 | `traffic_cita_datex2`, `traffic_fr_dir_est`, `traffic_vdl_info` | CC0-1.0, etalab-2.0 |
| `gold_roadworks` | Mobilité | 333 | 2020-05-28 → 2027-03-01 | `roadworks_cita_current`, `roadworks_cita_planned`, `roadworks_vdl`, `roadworks_vdl_permits` | CC0-1.0 |
| `gold_transit_disruptions` | Mobilité | 12 | 2026-05-03 → 2026-11-24 | `bus_vdl_messages`, `rail_sncb_irail`, `rail_sncf_siri` | CC0-1.0, ODbL-1.0, unspecified |
| `gold_mobility_veloh` | Mobilité | 160 | 2025-05-28 → 2026-11-25 | `veloh_stations` | unspecified |
| `gold_mobility_parkings` | Mobilité | 87 | 2026-11-25 → 2026-11-25 | `parkings_vdl` | CC0-1.0 |
| `gold_chargy_stations` | Mobilité | 1,572 | 2026-11-25 → 2026-11-25 | `chargy_stations` | CC0-1.0 |
| `gold_aviation` | Mobilité | 21 | 2026-11-25 → 2026-11-25 | `aviation_opensky` | unspecified |
| `gold_fuel_prices` | Économie | 70 | 2026-01 → 2026-10 | `fuel_prices_lu` | CC0-1.0 |
| `gold_inflation` | Économie | 946 | 1948-01 → 2026-10 | `inflation_ipcn_statec` | CC-BY-4.0 |
| `gold_electricity_spot` | Économie | 46,971 | 2024-12-31 → 2026-11-25 | `electricity_spot_delu` | CC-BY-4.0 |
| `gold_unemployment` | Économie | 36,186 | 2012-01 → 2026-10 | `unemployment_adem` | CC0-1.0 |
| `gold_building_permits` | Logement | 1,040 | 2010 → 2025 | `building_permits_statec` | CC-BY-4.0 |
| `gold_housing_prices` | Logement | 3,382 | 2010 → 2025 | `housing_prices_apartments`, `housing_prices_houses` | CC0-1.0 |
| `gold_holidays` | Calendrier | 435 | 2020-01-01 → 2036-12-26 | `holidays_be`, `holidays_de`, `holidays_fr`, `holidays_lu`, `school_holidays_lu` | CC0-1.0, unspecified |
| `gold_equipment` | Territoire | 1,021 | 2026-11-25 → 2026-11-25 | `aed_osm`, `bike_routes_regional`, `recycling_centers` | CC0-1.0, ODbL-1.0 |
| `gold_petitions` | Vie civique | 3,146 | 2006-07-17 → 2025-03-11 | `petitions_chd` | CC0-1.0 |
| `gold_culture_events` | Culture | 1,118 | 2026-01-07 → 2028-04-15 | `culture_echo_lu`, `events_rockhal`, `events_vdl_agenda` | unspecified |
| `gold_strikes_news` | Actualité | 44 | 2013-11-05 → 2026-10-11 | `strikes_news` | unspecified |
| `gold_luxembourg_daily_context` | Synthèse | 924 | 2026-09-10 → 2026-11-25 |  |  |

## Registre des 45 sources

| Source | Nature | Licence | URL primaire | Backup | Limites connues |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `meteo_findel_meteolux` | official | CC0-1.0 | https://metapi.ana.lu/api/v1/hvd/observations | https://data.public.lu/fr/datasets/r/0e03052d-0506-481d-8fd8-98d670103204 | Une seule station (Findel) ; instantané sans archive : l'historique est construit par accumulation. |
| `meteo_cantons_openmeteo` | model | CC-BY-4.0 | https://api.open-meteo.com/v1/forecast | — | Données de modèle (point de grille), pas des mesures de station ; heures sans valeur ignorées. |
| `air_quality_openmeteo` | model | CC-BY-4.0 | https://air-quality-api.open-meteo.com/v1/air-quality | — | Modèle CAMS Europe, pas des mesures : le réseau télémétrique AEV est figé depuis le 13/12/2025. |
| `pollen_openmeteo` | model | CC-BY-4.0 | https://air-quality-api.open-meteo.com/v1/air-quality | — | Modèle CAMS ; hors saison pollinique les valeurs sont nulles ou absentes. |
| `water_levels_age` | official | CC0-1.0 | https://inondations.public.lu/dam-assets/ctie/datas/Water-Levels-LocalTime.csv | https://data.public.lu/fr/datasets/r/94fecbb1-4fce-4bee-8f2d-fc03b9fa314f | Fenêtre glissante de 7 jours ; Esch-Sûre est exprimé en m (barrage), les autres en cm ; pas de débit. |
| `bathing_status_age` | official | CC0-1.0 | https://features.geoportail.lu/collections/656/items | — | Statut 'hors saison' hors période estivale. |
| `bathing_quality_age` | official | CC0-1.0 | https://features.geoportail.lu/collections/581/items | — | Classement annuel. |
| `traffic_cita_datex2` | official | CC0-1.0 | https://www.cita.lu/info_trafic/datex/situationrecord | https://cita.lu/info_trafic/datex/situationrecord36 | Autoroutes et voies express uniquement. |
| `traffic_vdl_info` | official | CC0-1.0 | https://maps.vdl.lu/arcgis/rest/services/DYNDATA/TRAFIC_INFO/FeatureServer/0/query | — | Territoire de la Ville de Luxembourg uniquement. |
| `traffic_fr_dir_est` | official | etalab-2.0 | http://tipi.bison-fute.gouv.fr/bison-fute-ouvert/publicationsDIR/Evenementiel-DIR/grt/RRN/content.xml | — | Réseau non concédé ; filtré sur la boîte Lorraine nord (lat 48,85–49,6). |
| `traffic_de_a1` | official | unspecified | https://verkehr.autobahn.de/o/autobahn/A1/services/warning | https://verkehr.autobahn.de/o/autobahn/A1/services/closure | Filtré sur la zone lat 49,3–50,1 / lon 6,0–7,2 ; licence non précisée par l'API. |
| `traffic_de_a8` | official | unspecified | https://verkehr.autobahn.de/o/autobahn/A8/services/warning | https://verkehr.autobahn.de/o/autobahn/A8/services/closure | Filtré sur la zone frontalière ; licence non précisée par l'API. |
| `traffic_de_a64` | official | unspecified | https://verkehr.autobahn.de/o/autobahn/A64/services/warning | https://verkehr.autobahn.de/o/autobahn/A64/services/closure | Liste souvent vide (aucune perturbation) ; licence non précisée par l'API. |
| `rail_sncf_siri` | official | ODbL-1.0 | https://proxy.transport.data.gouv.fr/resource/sncf-siri-lite-situation-exchange | — | Filtré par mots-clés (Luxembourg, Thionville, Metz, Bettembourg…). |
| `rail_sncb_irail` | community | unspecified | https://api.irail.be/disturbances/ | — | API communautaire iRail (non officielle) ; licence non précisée. |
| `bus_vdl_messages` | official | CC0-1.0 | https://web.vdl.lu/autobus/data/messages/messages.xml | — | Réseau AVL uniquement ; pas de temps réel RGTR/CFL/TICE sans clé API. |
| `veloh_stations` | official | unspecified | https://api.jcdecaux.com/vls/v3/stations | https://api.cyclocity.fr/contracts/luxembourg/gbfs/v2/station_status.json | Primaire JCDecaux v3 avec clé (JCDECAUX_API_KEY) ; backup GBFS sans clé, positions via le seed GBFS. |
| `parkings_vdl` | official | CC0-1.0 | https://feed.vdl.lu/circulation/parking/feed.json | — | Parkings gérés/relayés par la Ville uniquement. |
| `chargy_stations` | official | CC0-1.0 | https://my.chargy.lu/b2bev-external-services/resources/kml | — | Réseau Chargy uniquement. POURQUOI clé en clair : elle est publiée dans le catalogue CC0 data.public.lu. |
| `aviation_opensky` | community | unspecified | https://opensky-network.org/api/states/all | — | Instantané ; couverture ADS-B communautaire ; quota d'appels anonymes limité. |
| `roadworks_cita_current` | official | CC0-1.0 | https://www.cita.lu/info_trafic/datex/chantierActuelDatex.xml | — | Commentaires bruts du producteur (certains accents perdus à la source). |
| `roadworks_cita_planned` | official | CC0-1.0 | https://www.cita.lu/info_trafic/datex/chantierFuturDatex.xml | — | Dates prévisionnelles susceptibles d'évoluer. |
| `roadworks_vdl` | official | CC0-1.0 | https://maps.vdl.lu/arcgis/rest/services/DYNDATA/TRAFIC_INFO/FeatureServer/1/query | — | Territoire de la Ville uniquement ; position = centroïde de l'emprise. |
| `roadworks_vdl_permits` | official | CC0-1.0 | https://maps.vdl.lu/arcgis/rest/services/DYNDATA/TRAFIC_INFO/FeatureServer/5/query | — | Territoire de la Ville uniquement. |
| `fuel_prices_lu` | official | CC0-1.0 | https://data.public.lu/fr/datasets/r/d3a17cf8-5afc-4bf5-8222-9519e343d29d | — | Moyennes mensuelles de l'année en cours ; unités différentes selon l'énergie (l, kg, kWh). |
| `inflation_ipcn_statec` | official | CC-BY-4.0 | https://lustat.statec.lu/rest/data/LU1,DSD_PRIX_CONSO@DF_E5100,1.0/all | — | Publication mensuelle avec ~1 mois de décalage. |
| `electricity_spot_delu` | official | CC-BY-4.0 | https://api.energy-charts.info/price | — | Zone de marché commune Allemagne-Luxembourg. |
| `building_permits_statec` | official | CC-BY-4.0 | https://lustat.statec.lu/rest/data/LU1,DF_D4113/all | — | Granularité cantonale et annuelle. |
| `housing_prices_apartments` | official | CC0-1.0 | https://data.public.lu/fr/datasets/r/1d20f982-57e1-4ae2-a278-dc78c88c21dc | — | Prix annoncés (pas de transaction) ; masqués sous 30 annonces ; noms de communes historiques avant fusions. |
| `housing_prices_houses` | official | CC0-1.0 | https://data.public.lu/fr/datasets/r/14b0156e-ff87-4a36-a867-933fc9a6f903 | — | Prix annoncés (pas de transaction) ; masqués sous 30 annonces ; noms de communes historiques avant fusions. |
| `unemployment_adem` | official | CC0-1.0 | https://data.public.lu/fr/datasets/r/7bc964ea-7744-4860-ae84-24cc0ef3777d | — | Noms de communes d'avant fusion sur les périodes anciennes. |
| `holidays_lu` | official | CC0-1.0 | https://data.public.lu/fr/datasets/r/9dd69c71-f55e-4124-87b8-4a54ba528335 | https://openholidaysapi.org/PublicHolidays | Les jours de congé d'usage (non légaux) ne sont pas inclus. |
| `school_holidays_lu` | community | unspecified | https://openholidaysapi.org/SchoolHolidays | — | Source communautaire alimentée depuis les calendriers officiels. |
| `holidays_fr` | community | unspecified | https://openholidaysapi.org/PublicHolidays | — | Source communautaire. |
| `holidays_be` | community | unspecified | https://openholidaysapi.org/PublicHolidays | — | Source communautaire. |
| `holidays_de` | community | unspecified | https://openholidaysapi.org/PublicHolidays | — | Source communautaire ; libellés en allemand. |
| `weather_warnings_meteoalarm` | official | CC-BY-4.0 | https://feeds.meteoalarm.org/api/v1/warnings/feeds-luxembourg | — | Inclut les messages d'annulation ; LU-Alert (CAP) non intégré car sans URL 'dernière alerte' stable. |
| `aed_osm` | community | ODbL-1.0 | https://overpass.kumi.systems/api/interpreter | https://overpass-api.de/api/interpreter | Aucun jeu officiel : données OSM (ODbL), complétude non garantie ; serveurs Overpass parfois saturés. |
| `recycling_centers` | official | CC0-1.0 | https://data.public.lu/fr/datasets/r/be8c3b2e-88d3-4ddb-955c-40b354123d29 | — | Pas d'horaires ; coordonnées reprojetées depuis EPSG:3035. |
| `bike_routes_regional` | official | CC0-1.0 | https://data.geoportail.lu/mymaps | — | Réseau régional ; pas de couche nationale unique en GeoJSON. |
| `petitions_chd` | official | CC0-1.0 | https://data.public.lu/fr/datasets/r/6c43ab5c-8fc2-493b-822a-35793ac1c840 | — | Jeu non mis à jour depuis le 28/03/2025 (dernier dépôt 12/03/2025) ; motivations exclues. |
| `culture_echo_lu` | community | unspecified | https://py7g9mvxe2-dsn.algolia.net/1/indexes/prod_experiences.compact | — | Index de recherche public limité à 1000 résultats par requête ; conditions de réutilisation non publiées. |
| `events_vdl_agenda` | official | unspecified | https://www.vdl.lu/fr/agenda/rss.xml | — | Pas de lieu structuré ; pubDate utilisée comme date de l'événement. |
| `events_rockhal` | official | unspecified | https://rockhal.lu/wp-json/rockhal/shows | — | API WordPress non documentée. |
| `strikes_news` | press | unspecified | https://news.google.com/rss/search | https://www.rtl.lu/rss/national | Agrégateur de presse : titre et lien uniquement (factual-only) ; pays déduit par mots-clés. |

## Domaines sans source fiable (retirés)

- **Radioactivité ambiante** : les valeurs EURDEP/REMAP exigent une authentification ; seule la liste des 14 sondes est publique.
- **Bruit** : cartes stratégiques (polygones) sans série temporelle exploitable.
- **Trafic wallon (E411/E25)** : le flux DATEX II exige des identifiants.
- **Temps réel RGTR/CFL/TICE** : l'API mobiliteit.lu exige une clé `accessId`.
- **Ouvertures dominicales** : aucune source machine-lisible.
- **LU-Alert** : publié en CAP sur data.public.lu, mais sans URL stable « dernière alerte » (un fichier par alerte).
- **Agendas visitluxembourg, Luxexpo, Stade, Coque** : aucune donnée structurée (ni API ni JSON-LD).
