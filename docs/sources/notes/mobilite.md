# Sources ouvertes mobilité Luxembourg (vérifiées live le 2026-11-24)

Méthode : chaque URL marquée **VÉRIFIÉ** a été appelée avec `curl.exe -s -L` le 2026-11-24 (~21h45 CET) ; le code HTTP, le content-type, la taille et les premiers octets sont notés. Les métadonnées data.public.lu (licence, organisation, fréquence) viennent de l'API `https://data.public.lu/api/1/datasets/?q=...`. Les métadonnées transport.data.gouv.fr viennent de `https://transport.data.gouv.fr/api/datasets`.

Constat important pour le dépôt : plusieurs URLs actuellement dans `config/sources.toml` semblent inventées et n'apparaissent dans aucun catalogue : `https://data.public.lu/fr/datasets/r/mobiliteit-transit-live.json`, `https://api.mobiliteit.lu/v1/disruptions`, `https://data.public.lu/fr/datasets/r/chargy-live-stations.json`, `https://api.chargy.lu/v1/stations/status`. Je ne les ai pas testées une à une. Elles ne suivent pas le format UUID des ressources data.public.lu, et aucune n'apparaît dans les résultats de l'API du catalogue.

## 1. Trafic routier transfrontalier (FR A31 / DE A64-A1-A8 / BE E411-E25 / LU)

### Takeaway
France (Bison Futé DATEX II) et Allemagne (API Autobahn GmbH) sont accessibles sans clé et fonctionnent. La Wallonie n'a **pas** de flux public sans identifiants. Côté LU, le flux Cita DATEX II (PCH) est la meilleure source primaire pour les autoroutes luxembourgeoises.

### Cited Findings
**Allemagne — API Autobahn GmbH (sans clé, JSON) — VÉRIFIÉ**
- `https://verkehr.autobahn.de/o/autobahn/` → 200 JSON `{"roads":["A1","A2",...]}` (liste des autoroutes). — [Autobahn API](https://verkehr.autobahn.de/o/autobahn/)
- `https://verkehr.autobahn.de/o/autobahn/A64/services/roadworks` → 200 `{"roadworks":[]}` (vide ce jour) ; `.../A64/services/warning` → 200 `{"warning":[]}`. Une liste vide est une réponse valide, ce n'est pas une erreur. — [A64 roadworks](https://verkehr.autobahn.de/o/autobahn/A64/services/roadworks)
- `https://verkehr.autobahn.de/o/autobahn/A8/services/closure` → 200, 14,9 KB. Le 1er élément est `"title":"A8 | Perl - Pellinger Berg"`, `"subtitle":" Luxemburg -> Saarlouis"`, `"coordinate":{"lat":49.487,"long":6.415}`, `"future":true`, `description` = liste de lignes texte ("28.11.26 von 00:00 bis 05:00 Uhr"). — [A8 closure](https://verkehr.autobahn.de/o/autobahn/A8/services/closure)
- `https://verkehr.autobahn.de/o/autobahn/A1/services/warning` → 200, 6,4 KB. Champs : `identifier, icon, isBlocked ("false" en chaîne), future, extent ("lat,lon,lat,lon"), point ("lat,lon"), startLcPosition, display_type, subtitle, title, startTimestamp` (présent sur les warnings, ABSENT sur les closures). — [A1 warning](https://verkehr.autobahn.de/o/autobahn/A1/services/warning)
- Les clés d'une closure sont `coordinate, description, display_type, extent, footer, future, geometry, icon, identifier, impact, isBlocked, lorryParkingFeatureIcons, point, routeRecommendation, startLcPosition, subtitle, title`. — [A8 closure](https://verkehr.autobahn.de/o/autobahn/A8/services/closure)
- Pattern : `/o/autobahn/{road}/services/{roadworks|warning|closure|...}` ; enveloppe JSON = `{"<service>": [ ... ]}`. Coordonnées WGS84. L'A1 couvre toute l'Allemagne (436 KB pour les roadworks) : il faut filtrer par bbox près de Trèves (par ex. lat 49.4–50.0, lon 6.0–7.0).

**France — Bison Futé / DIR (réseau non concédé, inclut l'A31 Metz–Thionville–frontière) — VÉRIFIÉ**
- Événements : `http://tipi.bison-fute.gouv.fr/bison-fute-ouvert/publicationsDIR/Evenementiel-DIR/grt/RRN/content.xml` → 200 application/xml, 2,76 MB. C'est une enveloppe SOAP contenant un `d2LogicalModel` DATEX II v2 (namespace `http://datex2.eu/schema/2/2_0`, préfixe `ns2`). Le flux contient 4 mentions d'"A31" ce jour, par exemple un événement à Atton (lat 48.880287, lon 6.096598), `tpegDirection` northBound, commentaire "De Lyon vers Luxembourg". Coordonnées en WGS84 dans `pointCoordinates/latitude|longitude`. — [content.xml](http://tipi.bison-fute.gouv.fr/bison-fute-ouvert/publicationsDIR/Evenementiel-DIR/grt/RRN/content.xml) ; dataset "Événements routiers - Réseau routier non concédé", licence `lov2` (Licence Ouverte v2) — [transport.data.gouv.fr](https://transport.data.gouv.fr/datasets/62558686864eeafd3af07eac)
- Vitesses/débits : `http://tipi.bison-fute.gouv.fr/bison-fute-ouvert/publicationsDIR/QTV-DIR/qtvDir.xml` → 200, 1,4 MB, DATEX II v2 `MeasuredDataPublication`. Le référentiel des stations est `.../QTV-DIR/refDir.csv` (200 text/csv, 121 KB, séparateur `;`). Colonnes : `code_pme;source;source_2;code_insee_commune;axe;pr_debut;abscisse_debut;pr_fin;abscisse_fin;sens_gestionnaire;...;x_deb;y_deb;x_fin;y_fin;code_traficolor`. Il contient des lignes `axe=A31` de DIRE (par ex. `MZE54.22`). Les x/y semblent en Lambert-93 (par ex. 569981.6 ; non confirmé). — [qtvDir.xml](http://tipi.bison-fute.gouv.fr/bison-fute-ouvert/publicationsDIR/QTV-DIR/qtvDir.xml), [refDir.csv](http://tipi.bison-fute.gouv.fr/bison-fute-ouvert/publicationsDIR/QTV-DIR/refDir.csv) ; dataset lov2 — [transport.data.gouv.fr](https://transport.data.gouv.fr/datasets/626113a9e7a3010e25422e7f)
- Seul HTTP fonctionne : les URLs sont publiées en `http://` dans le catalogue, et je n'ai pas testé HTTPS.

**Luxembourg — Cita (Administration des Ponts et Chaussées), CC0 — VÉRIFIÉ**
- Événements DATEX II v3.6 : `https://cita.lu/info_trafic/datex/situationrecord36` → 200 text/xml, 98,7 KB. Racine `d2:payload xsi:type="sit:SituationPublication"` (namespaces DATEX II v3), `com:publicationTime` 2026-11-24T21:45:01+01:00, description "Active and planned events on Luxembourg highways". — [data.public.lu](https://data.public.lu/fr/datasets/cita-evenements-trafic-en-datex-ii-v3-6/)
- Ancien flux v2 des événements : `https://www.cita.lu/info_trafic/datex/situationrecord`. Je l'ai trouvé dans le catalogue mais je n'ai pas lu son corps. — [data.public.lu](https://data.public.lu/fr/datasets/cita-evenements-trafic-en-datex-ii/)
- Trafic mesuré par autoroute : `https://www.cita.lu/info_trafic/datex/trafficstatus_a13` → 200 text/xml, 221 KB, DATEX II v2 `MeasuredDataPublication`, supplier `lu/PCH`. Il existe aussi `trafficstatus_a7`, `_a6`, `_b40` (je n'ai testé que l'A13). Licence cc-zero, fréquence continue. — [data.public.lu](https://data.public.lu/fr/datasets/cita-donnees-trafic-en-datex-ii/)
- Comptages annuels PCH (xlsx, 2022–2025), par ex. `https://download.data.public.lu/resources/pch-comptage-trafic/20260427-044456/donneestrafic-2025.xlsx` (lien de catalogue, non téléchargé ; xlsx nécessiterait une dépendance hors liste). — [data.public.lu](https://data.public.lu/fr/datasets/pch-comptage-trafic/)

**Belgique — Wallonie E411/E25 : PAS de source sans clé trouvée**
- Le flux DATEX II "Événements routiers wallons" sur transportdata.be est livré en push HTTP(S). Il exige un nom d'utilisateur et un mot de passe, obtenus en contactant le propriétaire du dataset. — [transportdata.be](https://transportdata.be/dataset/walloon-road-traffic-events/resource/1aa4fc01-4dbc-420b-945c-558e0c18342a)

### Inferences
- Primaire DE = API Autobahn (A64, A1, A8 filtrés par bbox). Backup DE : aucun second flux DE sans clé n'a été testé ; Bison Futé ne couvre pas l'Allemagne.
- Primaire FR = Bison Futé `content.xml` filtré sur A31 ; backup FR = `qtvDir.xml` + `refDir.csv` (vitesses A31).
- Primaire LU = Cita `situationrecord36` ; backup LU = `trafficstatus_a*`.

### Gaps
- La licence de l'API Autobahn n'est pas indiquée dans la réponse et je ne l'ai pas vérifiée.
- Wallonie : il faut des identifiants. Le flux flamand (Verkeerscentrum Vlaanderen) n'a pas été testé et ne couvre pas l'E411/E25 côté Luxembourg.
- HTTPS pour tipi.bison-fute.gouv.fr : non testé.

## 2. Rail transfrontalier (Metz / Trèves / Arlon)

### Takeaway
SNCF publie, sans clé et via le proxy transport.data.gouv.fr, des flux GTFS-RT (alertes et trip updates) et SIRI Lite (situation exchange) qui couvrent le TER Metz–Luxembourg. Pour Arlon, l'API communautaire iRail (SNCB) est sans clé. Je n'ai trouvé aucun flux temps réel CFL public.

### Cited Findings
- `https://proxy.transport.data.gouv.fr/resource/sncf-gtfs-rt-service-alerts` → 200 `application/x-protobuf`, 782 KB (FeedMessage GTFS-RT 1.0 ; un décodeur protobuf est nécessaire). — [transport.data.gouv.fr dataset 6853c089b3ed5781f6adfdf7](https://transport.data.gouv.fr/datasets/6853c089b3ed5781f6adfdf7), licence `odc-odbl`
- `https://proxy.transport.data.gouv.fr/resource/sncf-gtfs-rt-trip-updates` → 200 protobuf, 419 KB. — même dataset
- `https://proxy.transport.data.gouv.fr/resource/sncf-siri-lite-situation-exchange` → 200 text/xml, 3,4 MB. Racine `<Siri version="2.0">/ServiceDelivery/ResponseTimestamp` (2026-11-24T20:47:20). Le texte contient "Luxembourg rail network" et 8 occurrences de "Thionville". **C'est le backup le plus simple à parser : XML, sans protobuf.** — même dataset
- Aussi disponible sans clé : `https://proxy.transport.data.gouv.fr/resource/sncf-siri-lite-estimated-timetable` (catalogue, non testé). — même dataset
- iRail (SNCB, Arlon) : `https://api.irail.be/disturbances/?format=json&lang=fr` → 200 JSON, 49 KB. Structure : `{"version":"1.4","timestamp":"<epoch s>","disturbance":[{"id","title","description","type":"disturbance","link",...}]}`. Les perturbations couvrent tout le réseau belge, il faut filtrer sur "Arlon"/"Luxembourg". — [iRail disturbances](https://api.irail.be/disturbances/?format=json&lang=fr)
- `https://api.irail.be/liveboard/?station=Arlon&format=json&lang=fr` → 200 JSON. `stationinfo.id` = `BE.NMBS.008866001`, `departures.departure[].station` (par ex. "Luxemb..."). — [iRail liveboard](https://api.irail.be/liveboard/?station=Arlon&format=json&lang=fr)
- Le GTFS statique LU contient l'agence `11,"Chemins de Fer Luxembourgeois"` (voir §3). Les horaires CFL transfrontaliers y figurent, mais sans temps réel.

### Inferences
- Primaire = SNCF SIRI Lite situation-exchange, filtré sur Luxembourg/Thionville/Metz. Backup = iRail disturbances, filtré sur Arlon/Luxembourg.
- Trèves (DB) : aucune source DB sans clé n'a été testée.

### Gaps
- La licence d'iRail n'est pas indiquée dans la réponse et je ne l'ai pas vérifiée (projet communautaire, non officiel).
- GTFS-RT CFL/mobiliteit : une réutilisation de 2017 sur data.public.lu le mentionne, mais je n'ai trouvé aucune URL publique ([data.public.lu reuse](https://data.public.lu/fr/reuses/gtfs-rt)).
- `https://www.cfl.lu/fr-fr/rss/disruptions` → **500** (page HTML d'erreur). URL devinée, non valide : je n'ai pas trouvé de RSS CFL.

## 3. Transport public Luxembourg

### Takeaway
Le GTFS statique de l'ATP est vérifié, CC-BY, hebdomadaire. Le temps réel officiel (HAFAS) exige une clé `accessId`. Le flux sans clé le plus utile pour les perturbations est le XML des messages AVL des bus de la Ville de Luxembourg.

### Cited Findings
- Dataset "Horaires et arrêts des transport publics (GTFS)", Administration des transports publics, licence `cc-by`, fréquence `weekly`, 346 ressources (une par semaine, historique conservé). — [data.public.lu](https://data.public.lu/fr/datasets/horaires-et-arrets-des-transport-publics-gtfs/)
- Dernière ressource : `https://data.public.lu/fr/datasets/r/1c0b65c7-44cf-4b71-a0e2-b21fffdcd155` → redirige vers `https://download.data.public.lu/resources/horaires-et-arrets-des-transport-publics-gtfs/20261120-065017/gtfs-20261119-20261212.zip` (200, 16,1 MB). Fichiers : `agency, calendar, calendar_dates, frequencies, routes, shapes, stop_times, stops, transfers, trips` (.txt). Les agences incluent RGTR (1), Ville de Luxembourg (6), CFL (11) et TICE (16). `agency_timezone` = "Europe/Berlin". `stops.txt` : `stop_id,stop_code,stop_name,stop_desc,stop_lat,stop_lon,location_type,parent_station,wheelchair_boarding,platform_code` (WGS84). — [resource](https://data.public.lu/fr/datasets/r/1c0b65c7-44cf-4b71-a0e2-b21fffdcd155)
- **Il n'existe pas d'URL « latest » stable** : l'UUID change chaque semaine. Pour obtenir le dernier fichier, interroger `https://data.public.lu/api/1/datasets/horaires-et-arrets-des-transport-publics-gtfs/` et prendre `resources[0].url` (VÉRIFIÉ ; la ressource porte aussi `filesize` et `checksum` md5).
- API HAFAS mobiliteit.lu : `https://cdt.hafas.de/opendata/apiserver/departureBoard?...&format=json` → **400** `errorCode="API_PARAM" errorText="Missing value for required param accessId"`. Une clé est donc obligatoire (à demander à l'ATP). Dataset "API mobiliteit.lu", cc-by. — [data.public.lu](https://data.public.lu/fr/datasets/api-mobiliteit-lu/)
- Messages AVL des bus VdL : `https://web.vdl.lu/autobus/data/messages/messages.xml` → 200 application/xml, 154 KB. Structure `<Messages><Message><MessageID>5334</MessageID><DateDebut>2026-05-03 04:00</DateDebut><DateFin>2027-02-01 05:00</DateFin><Urgent>true</Urgent><Categorie>Travaux</Categorie><Titre>…</Titre><TitreDE>…</TitreDE>…`. Les dates sont en heure locale, sans fuseau horaire. Licence cc-zero, Ville de Luxembourg. — [data.public.lu](https://data.public.lu/fr/datasets/mobilite-avl-autobus/)
- Les tracés des lignes et les arrêts VdL sont disponibles en GeoJSON (ArcGIS FeatureServer 10/11, `outSR=4326`). Je les ai trouvés dans le catalogue mais ne les ai pas testés. — même dataset
- Bonus vérifié : P+R CFL `https://pr-mobile-a.cfl.lu/OpenData/ParkAndRide/` → 200 JSON, tableau `[{"id":"RDWRW","name":"Rodange ","address":{...},"totalCapacity":1553,"wgS84Coordinate":{"longitude":5.845068,"latitude":49.552035}}, ...]`, licence `other-open` ; le détail par id est à `/OpenData/ParkAndRide/{id}` et il existe aussi un flux DATEX II `https://pr-mobile-a.cfl.lu/DatexII` (non testés). — [data.public.lu](https://data.public.lu/fr/datasets/liste-des-p-r-cfl/)
- Bonus vérifié : Flex carsharing CFL, CSV `;` mis à jour en continu (ressource du 2026-11-24). Colonnes : `car_type;fuel_type;available;brand_name;model_name;station_name;station_town;station_zipcode;station_street;station_streetnumber;station_latitude;station_longitude;createdDate`, licence cc-by. L'URL change à chaque mise à jour (même logique que le GTFS : passer par l'API). — [data.public.lu](https://data.public.lu/fr/datasets/flex-carsharing-by-cfl-1/)

### Inferences
- Primaire perturbations = messages AVL VdL (bus de la capitale uniquement) ; backup = SNCF SIRI SX pour les trains transfrontaliers. Il n'y a pas de couverture sans clé pour RGTR/TICE en temps réel.
- Primaire statique = GTFS via l'API data.public.lu ; backup = la ressource précédente du même dataset.

### Gaps
- Aucun GTFS-RT LU public trouvé.
- Le dataset NeTEx de l'ATP n'a pas été vérifié.

## 4. Bornes Chargy

### Takeaway
Le KML Chargy officiel fonctionne et donne la **disponibilité live par connecteur**. Il contient une clé API, mais celle-ci est publiée en clair dans le catalogue data.public.lu (CC0). Backup : DATEX II v3 multi-opérateurs d'Eco-Movement (avec un token public, lui aussi publié dans le catalogue) ou le GML INSPIRE du Géoportail.

### Cited Findings
- `https://my.chargy.lu/b2bev-external-services/resources/kml?API-KEY=486ac6e4-93b8-4369-9c6a-28f7c4e1a81f` → 200 `application/vnd.google-earth.kml+xml`, 695 KB, 524 `Placemark` (460 `#AVAILABLE`, 64 `#UNAVAILABLE`). Chaque Placemark contient `name`, `address`, `description` (HTML échappé : "4 connectors with 22kW… 3 available… 1 occupied"), `styleUrl` (#AVAILABLE/#UNAVAILABLE) et `ExtendedData/Data[name=CPnum]`. `Data[name=chargingdevice]/value` est du **JSON** : `{"id":10644,"name":"CP2500","numberOfConnectors":2,"connectors":[{"id":59985,"maxchspeed":22.08,"connector":1,"description":"CHARGING"},{"...":"AVAILABLE"}]}`. Le Placemark contient aussi `Point/coordinates` "lon,lat" (par ex. `5.97622,49.492728`). Dataset "Bornes de chargement publiques pour voitures électriques", organisation Chargy, licence `cc-zero`. — [data.public.lu](https://data.public.lu/fr/datasets/bornes-de-chargement-publiques-pour-voitures-electriques/)
- Eco-Movement : `https://api.eco-movement.com/api/nap/datexii/locations?token=S76EiFxqRLlZLCGBxHgyqUbaeKc5Pewb4HnRF1EeBV` → 200 text/xml, 941 KB, DATEX II v3 `d2:payload` (namespace `egi` energyInfrastructure). Licence `notspecified`. C'est un flux statique de localisations ; je n'ai pas vérifié s'il contient le statut. — [data.public.lu](https://data.public.lu/fr/datasets/bornes-de-chargement-publiques-pour-voitures-electriques-du-plusieurs-operateurs-1/)
- INSPIRE Géoportail, bornes électriques : `https://download.data.public.lu/resources/inspire-annex-i-theme-transport-networks-roads-roadnode-electrical-charging-stations/20261109-235504/tn.roadtransportnetwork.roadnode.electricalchargingstations.gml` → 200, 914 KB, GML 3.2 `FeatureCollection` (statique, cc-zero, ressource du 2026-11-09). — [data.public.lu](https://data.public.lu/fr/datasets/inspire-annex-i-theme-transport-networks-roads-roadnode-electrical-charging-stations/)

### Inferences
- Primaire = KML Chargy. Ces clés ne sont pas des secrets (elles sont publiées dans un catalogue CC0), mais il vaut mieux les mettre dans `config` avec un commentaire `# POURQUOI` plutôt que de les déguiser en `auth_env_var`.

### Gaps
- La fréquence de rafraîchissement du KML n'est pas documentée (le catalogue date la ressource de 2018-03-05, mais le contenu est live).
- Aucun endpoint JSON/GeoJSON Chargy officiel n'a été trouvé.

## 5. Pistes cyclables

### Takeaway
Plusieurs GeoJSON WGS84 sans clé ont été vérifiés : le réseau cyclable de la Ville de Luxembourg (ArcGIS) et les itinéraires régionaux et communaux du Géoportail (mymaps). Je n'ai pas trouvé de couche unique « pistes cyclables nationales » en GeoJSON.

### Cited Findings
- `https://data.geoportail.lu/mymaps?category=106&format=geojson` → 200 application/json, 2,7 MB, `FeatureCollection` "Pistes_cyclables_locales", 717 features LineString WGS84. Propriétés : `name` (par ex. "Regionaler Radweg Pratz - Buschrodt"), `color`, `linestyle`, `map_id`… Licence cc-zero, Direction générale du tourisme. — [data.public.lu](https://data.public.lu/fr/datasets/sentiers-cyclables-reseau-ditineraires-cyclables-regionaux/)
- `https://data.geoportail.lu/mymaps?category=197&format=geojson` (itinéraires communaux) → 200, 371 KB, FeatureCollection LineString ; licence `notspecified`. — [data.public.lu](https://data.public.lu/fr/datasets/sentiers-cyclables-reseau-ditineraires-cyclables-communaux/)
- `https://maps.vdl.lu/arcgis/rest/services/OPENDATA/GEOJSON/FeatureServer/23/query?where=1=1&outFields=*&outSR=4326&f=geojson` → 200 `application/geo+json`, 1,3 MB. Propriétés : `OBJECTID, OS, VELOROUTE_NR ("PC"), STATUS ("existent"), BEFAHRBARKEIT, STUFE ("Lokal"), BEMERKUNG, ABH_PKW_FAHRTR, CITYMAP, Shape__Length`. Licence cc-zero, Ville de Luxembourg. — [data.public.lu](https://data.public.lu/fr/datasets/mobilite-reseau-cyclable/)
- Points-nœuds du réseau cyclable national (PCH) : zip `pcnat-kp-num-202605.zip` (cc-zero, 2026-05-18). Trouvé dans le catalogue, non téléchargé. — [data.public.lu](https://data.public.lu/fr/datasets/point-noeuds-sur-le-reseau-cyclable-national-au-luxembourg/)
- Chantiers sur pistes cyclables, KML : `https://www.cita.lu/kml/chantiers_actuel_PC.kml` → 200, 69 KB (cc-zero). — [data.public.lu](https://data.public.lu/fr/datasets/pch-les-chantiers-actuels-des-pistes-cyclables/)

### Inferences
- Primaire national = mymaps catégorie 106 ; backup = VdL FeatureServer 23 (capitale uniquement) ou catégorie 197.

### Gaps
- Je n'ai pas trouvé de WFS PCH « pistes cyclables nationales » (PC1–PC…) ; la catégorie 106 est titrée régionale.

## 6. Vel'oh (JCDecaux GBFS)

### Takeaway
Les flux GBFS sont sans clé et vérifiés, en v2.3 et en v3.0.

### Cited Findings
- `https://api.cyclocity.fr/contracts/luxembourg/gbfs/gbfs.json` → 200, `version 2.3`, `ttl 3600`, langue `fr`. Les feeds listés sont `gbfs_versions`, `station_information`, `system_information`, `station_status`, `vehicle_types`… — [gbfs.json](https://api.cyclocity.fr/contracts/luxembourg/gbfs/gbfs.json)
- `https://api.cyclocity.fr/contracts/luxembourg/gbfs/v2/station_information.json` → 200, 21,8 KB, `ttl 300`. `data.stations[]` contient `station_id` ("1"), `name` ("#00001-LEON XIII"), `lat` 49.598211, `lon` 6.137526, `address`, `capacity` 20. — [station_information](https://api.cyclocity.fr/contracts/luxembourg/gbfs/v2/station_information.json)
- `https://api.cyclocity.fr/contracts/luxembourg/gbfs/v2/station_status.json` → 200, 40 KB, `ttl 5`. `data.stations[]` contient `station_id, num_bikes_available, vehicle_types_available[{vehicle_type_id:"electrical",count}], num_bikes_disabled, num_docks_available, num_docks_disabled, is_installed, is_renting, is_returning, last_reported` (epoch s). `last_updated` est un epoch en secondes (1795553170). — [station_status](https://api.cyclocity.fr/contracts/luxembourg/gbfs/v2/station_status.json)
- Backup : `https://api.cyclocity.fr/contracts/luxembourg/gbfs/v3/gbfs.json` → 200, `version 3.0`, `last_updated` au format ISO-8601 ("2026-11-24T20:31:24.27Z"). — [v3](https://api.cyclocity.fr/contracts/luxembourg/gbfs/v3/gbfs.json)

### Gaps
- La licence n'apparaît ni dans `gbfs.json` ni dans `system_information`, que je n'ai pas lu.

## 7. Météo (backup)

### Takeaway
L'endpoint JSON sans clé de l'app MeteoLux (ANA) fonctionne. Il n'est pas documenté comme open data.

### Cited Findings
- `https://metapi.ana.lu/api/v1/metapp/weather?lat=49.61&long=6.13` → 200 application/json, 27,6 KB. Structure : `{"city":{"id":456,"name":"Luxembourg","canton":"Luxembourg","lat":49.611567,"long":6.133836},"forecast":{"current":{"date":"2026-11-24T21:42:00","icon":{"id":7,"name":"Ciel dégagé"},"wind":{"direction":"NE","speed":"10-20","gusts":null},"rain":"0","snow":"0","temperature":{"temperature":-2,"felt":-6}},"hourly":[...]}}`. Sans paramètre → 422 "city or (lat,long) required" ; `city` attend un id entier. — [metapi](https://metapi.ana.lu/api/v1/metapp/weather?lat=49.61&long=6.13)
- Météo routière Cita en DATEX II : `https://www.cita.lu/info_trafic/datex/weather_dynamic.xml` → 200 text/xml, 67 KB, `MeasuredDataPublication`, cc-zero ; les stations sont dans `weather_static.xml` (non testé). — [data.public.lu](https://data.public.lu/fr/datasets/cita-donnees-meteo-en-datex-ii/)

### Gaps
- metapi.ana.lu : aucune licence ni documentation publique trouvée. C'est probablement l'API interne de l'app, à risque de changer. Le flux Cita weather_dynamic (CC0) est le backup sûr.
