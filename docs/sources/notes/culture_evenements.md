# Sources Culture / Événements / Actualités-Grèves Luxembourg (vérifiées 2026-11-24)

Toutes les URLs ci-dessous ont été testées le 2026-11-24 avec `curl.exe -s -L -A "Mozilla/5.0"`. Comptage JSON-LD = occurrences de `application/ld+json` et de `"@type":"...Event"` dans le HTML brut. « Vérifié » = HTTP 200 + contenu non vide. Licences : seules celles affichées par l'API/le portail sont citées ; le reste est en Gaps.

## 1. Agenda Ville de Luxembourg (VDL)

### Takeaway
Primaire : flux RSS agenda VDL (30 items, date de l'événement dans `pubDate`). Backup : index Algolia echo.lu filtré `communes:luxembourg` (1 950 événements). Pas d'iCal, pas de JSON-LD, rien sur data.public.lu pour l'agenda.

### Cited Findings
- `https://www.vdl.lu/fr/agenda/rss.xml` : HTTP 200, RSS 2.0, 30 `<item>`, `<ttl>60</ttl>`, `lastBuildDate` = 24 Nov 2026 21:47 +0100. Champs par item : `title` (CDATA), `link`, `description` (HTML long, éditorial → à exclure), `guid` (= URL), `pubDate` (ex. `Tue, 24 Nov 2026 17:30:00 +0100` pour « Mardis Littéraires - Tom Hillenbrand », semble être l'heure de début), `enclosure` (image). Pas de lieu structuré. Content-Type annoncé `text/html` malgré XML valide — [VDL agenda RSS](https://www.vdl.lu/fr/agenda/rss.xml)
- Lien RSS découvert dans le HTML de la page agenda (aussi `https://www.vdl.lu/fr/news/rss.xml`, 14 items, actualités) — [VDL agenda](https://www.vdl.lu/fr/agenda)
- `https://www.vdl.lu/fr/agenda` : 200, 0 bloc JSON-LD, 0 Event — [VDL agenda](https://www.vdl.lu/fr/agenda)
- `https://www.vdl.lu/fr/agenda/ical` et `https://www.vdl.lu/fr/rss.xml` : 404 — [VDL](https://www.vdl.lu/fr/agenda/ical)

### Inferences
- Le RSS ne donne que ~30 prochains événements (fenêtre glissante) : historique à accumuler par polling (cadence 60 min cohérente avec `ttl`). Clé de dédoublonnage = `guid`.
- Lieu absent → backup echo.lu (venue + geoloc) plus riche.

### Gaps
- Licence de réutilisation du flux VDL non trouvée (pas de mention dans le flux). Le site VDL publie d'autres jeux en open data mais je n'ai pas vérifié de licence spécifique à l'agenda.
- Sémantique exacte de `pubDate` (début de l'événement vs date de publication) déduite d'un seul exemple.

## 2. Salles culturelles (Rockhal, Philharmonie, den Atelier, Neimënster, Grand Théâtre)

### Takeaway
Seule Rockhal expose un JSON structuré exploitable (endpoint WordPress custom `/wp-json/rockhal/shows`, 81 shows à venir avec dates). Aucune salle testée n'émet de JSON-LD `Event`. den Atelier bloque curl (403). Pour les autres, le backup est echo.lu (filtre `rawExperience.venues`).

### Cited Findings
- **Rockhal primaire** `https://rockhal.lu/wp-json/rockhal/shows` : 200, JSON ~97 Ko, objet `{status[], genres[], shows[]}`, `shows` = 81 éléments. Champs : `id`, `permalink`, `title` (ex. `MAMMOTH`), `subtitle`, `start_date` (`"Tue 01 Dec 2026"`, texte), `end_date`, `show_year`, `show_month`, `location` (`"Rockhal Club"`), `organiser`, `status_string` (`buy-now`, `cancelled`, …), `availability`, `tm_id` (Ticketmatic), `published` (epoch). — [Rockhal shows JSON](https://rockhal.lu/wp-json/rockhal/shows)
- Rockhal WP REST standard `https://rockhal.lu/wp-json/wp/v2/show?per_page=100` : 200, `X-WP-Total: 2276`, 23 pages, mais `acf: []` → pas de date d'événement (seulement `date` de publication), utile seulement pour l'historique des titres/URLs. — [Rockhal WP show](https://rockhal.lu/wp-json/wp/v2/show?per_page=100)
- Rockhal pages HTML (home, `/shows/mastodon/`) : 1–2 JSON-LD Yoast (WebPage, Organization, BreadcrumbList), 0 Event ; `https://rockhal.lu/shows/` renvoie 404. — [Rockhal](https://rockhal.lu/)
- **Neimënster** `https://www.neimenster.lu/wp-json/wp/v2/events?per_page=100` : 200, `X-WP-Total: 1780`, 18 pages ; champs `id`, `date`, `modified`, `link`, `title.rendered`, taxonomies `event_discipline`, `event_type`, `event_thematic` ; `acf: []` → pas de date d'événement exposée. Page agenda : 1 JSON-LD (Yoast), 0 Event. — [Neimënster WP events](https://www.neimenster.lu/wp-json/wp/v2/events?per_page=100)
- **Philharmonie** `https://www.philharmonie.lu/en/programme` : 200, 0 JSON-LD ; heures en attributs HTML `data-event-start-time="10:30"` ; page détail (`/en/programme/2026-27/festival/familljefestival-dreams-0000013e00000590`) : 0 JSON-LD. — [Philharmonie programme](https://www.philharmonie.lu/en/programme)
- **den Atelier** `https://www.atelier.lu/` et `/concerts/` : 403 (protection anti-bot, ~5 Ko). — [den Atelier](https://www.atelier.lu/)
- **Grand Théâtre / Théâtres de la Ville** `https://www.theatres.lu/fr/programme` : 200, 68 Ko, 0 JSON-LD, aucun lien de fiche détectable (rendu probablement côté client). — [theatres.lu](https://www.theatres.lu/fr/programme)

### Inferences
- Rockhal : `start_date` est une chaîne localisée anglaise → parser `%a %d %b %Y`. Liste = uniquement à venir → accumuler par polling.
- Neimënster : l'API WP donne titre+URL mais pas la date de l'événement ; utiliser echo.lu comme source de dates.
- Philharmonie/GT/Atelier : scraping HTML fragile → passer par echo.lu.

### Gaps
- Aucune licence/CGU de réutilisation trouvée pour les API WordPress Rockhal/Neimënster (endpoints publics non documentés, susceptibles de changer).
- Je n'ai pas vérifié si ces salles sont présentes dans echo.lu (facette `rawExperience.venues` non énumérée).

## 3. Visit Luxembourg

### Takeaway
Aucune source machine-readable trouvée : pas de JSON-LD Event, pas d'API publique détectée.

### Cited Findings
- `https://www.visitluxembourg.com/events` et `/whats-on` : 404. — [Visit Luxembourg](https://www.visitluxembourg.com/events)
- Home `https://www.visitluxembourg.com/` : 200, 0 JSON-LD ; seul lien agenda : `/experience-luxembourg/festivals-events`. — [Visit Luxembourg](https://www.visitluxembourg.com/)
- `https://www.visitluxembourg.com/experience-luxembourg/festivals-events` : 200, 313 Ko, 0 JSON-LD, 0 trace d'Algolia/GraphQL/`/api/`. — [Festivals & events](https://www.visitluxembourg.com/experience-luxembourg/festivals-events)

### Gaps
- API interne éventuelle (XHR) non inspectée (nécessiterait un navigateur). Pas de source à recommander.

## 4. Luxexpo The Box, Stade de Luxembourg, d'Coque

### Takeaway
Aucun JSON-LD Event. luxexpo.lu injoignable (timeout) depuis ce poste. Les événements Luxexpo sont présents dans echo.lu (venue `luxexpo-the-box-qhEIB1`), qui sert de source de repli.

### Cited Findings
- `https://www.luxexpo.lu/`, `/en/agenda`, `/fr/agenda`, `https://luxexpo.lu/`, `https://www.luxexpo.com/` : code 000 (pas de réponse / timeout 20–25 s). — [luxexpo.lu](https://www.luxexpo.lu/)
- `https://www.stadedeluxembourg.lu/fr/agenda` : 200, 47 Ko, 0 JSON-LD, 3 liens d'événements (`/fr/agenda/luxembourg-bulgarie-1`, `luxembourg-estonie-0`, `luxembourg-islande-0`). — [Stade agenda](https://www.stadedeluxembourg.lu/fr/agenda)
- `https://www.coque.lu/en/` : 200, 0 JSON-LD (Drupal) ; `https://www.coque.lu/fr/agenda` : 404. — [d'Coque](https://www.coque.lu/en/)
- echo.lu contient un événement à `Luxexpo The Box` (EXPOGAST 2026, venue id `luxexpo-the-box-qhEIB1`, geoloc 49.636/6.173). — [echo Algolia](https://py7g9mvxe2-dsn.algolia.net/1/indexes/prod_experiences.compact?x-algolia-application-id=PY7G9MVXE2&x-algolia-api-key=55301c0ef2e535ae29e6b6d697f4882d&query=&hitsPerPage=1000)

### Gaps
- thebox.lu non testé (pas de réponse luxexpo). Raison du timeout luxexpo (géo-blocage, IP, panne) inconnue.

## 5. echo.lu (index Algolia `prod_experiences.compact`)

### Takeaway
Source la plus riche (3 646 expériences, 76 communes, dates, lieu, geoloc, gratuit/payant, prix). Limite dure : 1 000 hits par requête (`paginationLimitedTo: 1000`) ; `browse` interdit → il faut découper par fenêtres temporelles `numericFilters` pour tout récupérer. Licence/CGU non vérifiables.

### Cited Findings
- URL actuelle : 200, `application/json`, 11,9 Mo, `nbHits: 3646`, `nbPages: 1`, `hitsPerPage: 1000`, 1 000 hits retournés ; 971 avec `to_timestamp` ≥ maintenant. — [echo Algolia](https://py7g9mvxe2-dsn.algolia.net/1/indexes/prod_experiences.compact?x-algolia-application-id=PY7G9MVXE2&x-algolia-api-key=55301c0ef2e535ae29e6b6d697f4882d&query=&hitsPerPage=1000)
- Pagination : `page=1` avec `hitsPerPage=1000` (et `page=10` avec 100) → message « you can only fetch the 1000 hits for this query… use the browse method » ; `/browse` → 403 « Method not allowed with this API key ». — idem
- Filtre numérique fonctionnel : `numericFilters=to_timestamp>=1795996800000` → `nbHits: 3283`. — idem + `&numericFilters=to_timestamp%3E%3D1795996800000`
- Settings lisibles (`/1/indexes/prod_experiences.compact/settings`) : `paginationLimitedTo: 1000`, ranking `asc(alacSorting)`, `asc(from_timestamp)`; facettes : `communes`, `from_timestamp`, `to_timestamp`, `isFree`, `rawExperience.categories`, `rawExperience.venues`, `rawExperience.formats`, `rawExperience.languages`, `rawVenues.categories`, … — [settings](https://py7g9mvxe2-dsn.algolia.net/1/indexes/prod_experiences.compact/settings?x-algolia-application-id=PY7G9MVXE2&x-algolia-api-key=55301c0ef2e535ae29e6b6d697f4882d)
- `attributesToRetrieve` + `attributesToHighlight=` fonctionnent (réponse réduite) ; `facets=communes` → 76 communes, top : luxembourg 1 950, esch_sur_alzette 297, niederanven 234, wiltz 188, differdange 102. — idem
- Champs de premier niveau : `objectID`, `experienceId`, `from`/`to` (`{_seconds,_nanoseconds}`), `from_timestamp`/`to_timestamp` (ms epoch), `communes` (slugs), `_geoloc` [{lat,lng}], `isFree`, `isLuxembourgTicket`, `image`, `views`, `rawVenues[]` (`title`, `_geoloc`, `location`, `website`, `mainCategory`…), `rawExperience` (`title` multilingue `{en|fr|de}`, `dates[]`, `categories`, `formats`, `priceType`, `tickets[{price,title}]`, `purchaseLink`, `venues`, `status.current`, `moderation`, `description` éditorial, plus `contact`, `salesContact`, `timestamps.createdBy/updatedBy` → **PII potentielle à exclure**). Exemple : « EXPOGAST - RAK Porcelain Culinary World Cup 2026 », Luxexpo The Box, tickets 14 €. — idem

### Inferences
- Pour l'exhaustivité : boucler sur des fenêtres `numericFilters=from_timestamp>=A,from_timestamp<B` dont chacune < 1 000 hits (ex. mensuelles), avec `attributesToRetrieve=objectID,rawExperience.title,from_timestamp,to_timestamp,communes,_geoloc,isFree,rawExperience.priceType,rawVenues.title,rawExperience.venues` pour éviter 12 Mo et les champs PII/éditoriaux.
- Clé API = clé « search-only » publique embarquée dans le front d'echo.lu ; peut être tournée sans préavis.

### Gaps
- CGU echo.lu : `https://www.echo.lu/en/terms-and-conditions` renvoie 200 mais SPA de 4 Ko sans texte → conditions de réutilisation **non vérifiées**. L'usage d'une clé Algolia front-end n'est pas une licence explicite ; stocker uniquement des faits (titre ≤140, dates, lieu, URL) réduit le risque mais ne le supprime pas.

## 6. Grèves / perturbations sociales (RSS)

### Takeaway
Primaire : Google News RSS recherche (FR `grève Luxembourg` 49 items ; DE `Streik Luxemburg` 100 items ; requête transfrontalière 7 j 31 items). Backup : RTL.lu RSS national (28 items) + gouvernement.lu (50 items) filtrés par mots-clés. Pas de flux CFL/L'essentiel/Le Quotidien fonctionnel.

### Cited Findings
- `https://news.google.com/rss/search?q=gr%C3%A8ve+Luxembourg&hl=fr&gl=LU&ceid=LU:fr` : 200, `application/xml`, 49 items ; ex. « Treize trains supprimés entre Luxembourg et Metz jeudi - L'essentiel », « Grève en Belgique: plusieurs perturbations attendues… » ; champs `title`, `link` (redirection Google), `pubDate`, `source url=` (lessentiel.lu, virgule.lu, lequotidien.lu). — [Google News FR](https://news.google.com/rss/search?q=gr%C3%A8ve+Luxembourg&hl=fr&gl=LU&ceid=LU:fr)
- `https://news.google.com/rss/search?q=Streik+Luxemburg&hl=de&gl=LU&ceid=LU:de` : 200, 100 items (ex. « Streik legt Flugverkehr in Belgien lahm - Luxemburger Wort »). — [Google News DE](https://news.google.com/rss/search?q=Streik+Luxemburg&hl=de&gl=LU&ceid=LU:de)
- `https://news.google.com/rss/search?q=gr%C3%A8ve+(SNCF+OR+SNCB+OR+CFL+OR+frontaliers)+when:7d&hl=fr&gl=LU&ceid=LU:fr` : 200, 31 items. — [Google News transfrontalier](https://news.google.com/rss/search?q=gr%C3%A8ve+(SNCF+OR+SNCB+OR+CFL+OR+frontaliers)+when:7d&hl=fr&gl=LU&ceid=LU:fr)
- `https://www.rtl.lu/rss/national` : 200, 28 items (luxembourgeois). `https://www.rtl.lu/rss` : 200 mais HTML sans item ; `https://today.rtl.lu/rss/national` : 404. — [RTL national](https://www.rtl.lu/rss/national)
- `https://gouvernement.lu/fr/actualites/toutes_actualites.rss` : 200, 50 items (aucun titre grève aujourd'hui). `https://gouvernement.lu/fr/actualites.rss` : 200 mais 0 item. — [gouvernement.lu RSS](https://gouvernement.lu/fr/actualites/toutes_actualites.rss)
- `https://www.wort.lu/rss` : 200, 50 items (titres vides dans le canal). — [Wort RSS](https://www.wort.lu/rss)
- `https://www.mobiliteit.lu/fr/feed/` : 200, 10 items (actualités mobilité, pas de perturbations temps réel). — [mobiliteit.lu feed](https://www.mobiliteit.lu/fr/feed/)
- Échecs : `https://www.cfl.lu/fr-fr/rss` 500 ; L'essentiel (`/fr/rss`, `/rss`, `/fr/rss/luxembourg`, `partner-feeds…`) 404 ; `https://lequotidien.lu/feed/` 404 ; chronicle.lu RSS 0 item ; `mobiliteit.lu/fr/perturbations/feed/` 404. — [CFL](https://www.cfl.lu/fr-fr/rss)

### Inferences
- Google News agrège L'essentiel/Virgule/Quotidien/Wort, donc couvre les médias dont le RSS direct est cassé. `when:7d` limite le bruit ; dédoublonner sur `link`/`guid`.
- RTL/gouvernement.lu ne sont pas spécifiques grève → filtrer par regex (`grève|Streik|Grève|Gewerkschaft|OGBL|LCGB|manifestation`).

### Gaps
- CGU Google News RSS non vérifiées (usage personnel/non commercial historiquement ; à confirmer). Licence RTL/gouvernement.lu non vérifiée.
- Aucun flux officiel CFL de perturbations trouvé.

## 7. Référentiel des 100 communes (canton, coordonnées)

### Takeaway
data.public.lu « Limites administratives du Grand-Duché de Luxembourg » (CC0) fournit un CSV de 100 communes avec canton/district/code LAU2 et des GeoJSON (WGS84) pour calculer les centroïdes. Idéal pour valider le seed.

### Cited Findings
- Jeu de données CC0 (`license: cc-zero`) — [Limites administratives](https://data.public.lu/fr/datasets/limites-administratives-du-grand-duche-de-luxembourg/)
- CSV `commune-canton-district-circonscription-arrondissements.csv` (2024-07-09) : 101 lignes = 100 communes + en-tête ; colonnes `COMMUNE, CODE_LAU2, SURFACE_GEOMETRIQUE_COMMUNE_[m2], CANTON, DISTRICT, CIRCONSCRIPTION_ELECTORALE, ARRONDISSEMENT_JUDICIAIRE` ; ex. `Dalheim,1202,19172011,Remich,Grevenmacher,EST,LUXEMBOURG` (UTF-8 avec BOM). — [CSV](https://download.data.public.lu/resources/limites-administratives-du-grand-duche-de-luxembourg/20240709-164127/commune-canton-district-circonscription-arrondissements.csv)
- `limadmin.geojson` (mis à jour 2026-11-05) : objet à clés `cantons` (12 features), `communes` (100, props `COMMUNE, CANTON, DISTRICT, LAU2`), `districts` (3), `pays` (1) ; coordonnées en lon/lat (ex. 5.989, 50.175), pas de `crs` déclaré. Attention : ce n'est pas un FeatureCollection standard à la racine. — [limadmin.geojson](https://download.data.public.lu/resources/limites-administratives-du-grand-duche-de-luxembourg/20261105-040012/limadmin.geojson)
- `communes4326.geojson` (2023-11-23) : FeatureCollection standard, 100 features MultiPolygon, props `COMMUNE, CANTON, DISTRICT, LAU2`. — [communes4326.geojson](https://download.data.public.lu/resources/limites-administratives-du-grand-duche-de-luxembourg/20231123-101528/communes4326.geojson)
- Backup cantons : « Cantons in Luxembourg 2026 » (CC-BY) GeoJSON — [Cantons 2026](https://data.public.lu/fr/datasets/cantons-in-luxembourg-2026/)

### Inferences
- Coordonnées de commune = centroïde du polygone (pas de point officiel « chef-lieu » dans ces fichiers). URL de ressource datée → résoudre via l'API `https://data.public.lu/api/1/datasets/limites-administratives-du-grand-duche-de-luxembourg/` plutôt que coder l'URL en dur.

### Gaps
- Pas de jeu « coordonnées ponctuelles des chefs-lieux » vérifié ; Geoportail WFS non testé.
