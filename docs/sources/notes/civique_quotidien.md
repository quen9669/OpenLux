# Sources ouvertes Luxembourg vérifiées — domaines civiques et vie quotidienne

All tests below were run live with `curl.exe` on **2026-11-24**. Each line gives `HTTP code | content-type | bytes`. The `https://data.public.lu/fr/datasets/r/<uuid>` links are stable redirects to the latest file on `download.data.public.lu`. The `download.data.public.lu/.../<timestamp>/...` URLs change at each upload, so **use only the `/r/<uuid>` form**. The data.public.lu API is `https://data.public.lu/api/1/datasets/<id>/`.

## 1. Public holidays and school holidays

### Takeaway
Primary: data.public.lu "Jours fériés légaux au Luxembourg" (JSON/CSV/ICS, CC0, 2020 onwards, refreshed 2026-11-01). Backups: OpenHolidays API (also has LU school holidays and FR/BE/DE) and Nager.Date. For school holidays the primary is OpenHolidays, because the data.public.lu school-holiday datasets are weak.

### Cited Findings
- **PRIMARY public holidays, JSON**: `https://data.public.lu/fr/datasets/r/9dd69c71-f55e-4124-87b8-4a54ba528335` → `200 application/json 35174`. Array of `{"year":2020,"date":"2020-01-01","dayOfWeek":"Wednesday","en":"New Year's Day","fr":"Nouvel An","de":"Neujahr","lb":"Neijoerschdag"}`. Org "Open Data Lëtzebuerg", licence **cc-zero**, frequency annual, last update 2026-11-01 — [dataset 63849034f8622653897791a4](https://data.public.lu/api/1/datasets/63849034f8622653897791a4/)
- Same dataset, **CSV**: `https://data.public.lu/fr/datasets/r/a644fb1e-58c2-4800-8831-c24abdded142` → `200 text/csv 16382`. Header `year, date, day of week, name in english, name in french, name in german, name in luxembourgish`. The separator is comma+space, so strip whitespace when parsing. ICS files also exist: fr `924ad245-73ed-4ebb-ae8d-8d57fac4d26c`, lb `b91d5ecf-...`, de `ece73694-...`, en `5ae3a048-...` — [same dataset](https://data.public.lu/api/1/datasets/63849034f8622653897791a4/)
- **BACKUP public holidays, OpenHolidays**: `https://openholidaysapi.org/PublicHolidays?countryIsoCode=LU&languageIsoCode=FR&validFrom=2026-01-01&validTo=2026-12-31` → `200 application/json 2831`. Item: `{"id":"<uuid>","startDate":"2026-01-01","endDate":"2026-01-01","type":"Public"|"Bank","name":[{"language":"FR","text":"Nouvel An"}],"regionalScope":"National","temporalScope":"FullDay","nationwide":true}`. **Note**: Good Friday (Vendredi Saint) is returned with `type:"Bank"`, which is not a legal public holiday in LU, so filter on `type=="Public"`. No key needed — [OpenHolidays API](https://openholidaysapi.org/PublicHolidays?countryIsoCode=LU&languageIsoCode=FR&validFrom=2026-01-01&validTo=2026-12-31)
- **Second backup, Nager.Date**: `https://date.nager.at/api/v3/PublicHolidays/2026/LU` → `200 application/json 2103`. Item: `{"date","localName":"Neijoerschdag","name","countryCode":"LU","fixed","global":true,"counties":null,"launchYear":null,"types":["Public"]}`. Good Friday also comes as `types:["Bank"]` — [Nager.Date](https://date.nager.at/api/v3/PublicHolidays/2026/LU)
- **PRIMARY school holidays, OpenHolidays**: `https://openholidaysapi.org/SchoolHolidays?countryIsoCode=LU&languageIsoCode=FR&validFrom=2026-01-01&validTo=2027-12-31` → `200 application/json 2611`. Same structure with `type:"School"`, e.g. `"Vacances de Noël"` 2025-12-20→2026-01-04, `"Congé de Carnaval"` 2026-02-14→02-22, `"Vacances de Pâques"` 2026-03-28→04-12. For FR/BE/DE, change `countryIsoCode`; regional subdivisions appear under `subdivisions` (country list: `https://openholidaysapi.org/Countries` → 200) — [OpenHolidays](https://openholidaysapi.org/SchoolHolidays?countryIsoCode=LU&languageIsoCode=FR&validFrom=2026-01-01&validTo=2027-12-31)
- **BACKUP school holidays, EducDesign (data.public.lu, cc-zero)**: ICS `https://www.educdesign.lu/resources/calendar/1/calendar.ics` → `200 text/calendar 30001` (VCALENDAR, `X-WR-CALNAME:Vaka…`). RSS `https://www.educdesign.lu/olefarss?type=calendar&id=1` → `200 application/rss+xml 6172`. The legal-holidays version is calendar id=3. This is a private publisher (EducDesign S.A.) — [dataset 577f589d32cc2255638879b8](https://data.public.lu/api/1/datasets/577f589d32cc2255638879b8/)
- data.public.lu "Vacances Scolaires" (no organisation, licence `other-open`, last update 2025-09-27): JSON `827eb943-bf58-4f55-850b-53c1c215186a` → 200, but it is only a flat list of `{"Date":"30/10/2021"}` with no holiday name. CSV `cd076029-...` → `200 text/csv 8709`. Not recommended — [dataset 61d1d543a006178d20aaac04](https://data.public.lu/api/1/datasets/61d1d543a006178d20aaac04/)

### Inferences
- The data.public.lu JSON has 4-language labels and starts in 2020, which is enough history. OpenHolidays is the only keyless source that has LU school holidays with names and cross-border countries.

### Gaps
- I did not find any official MENJE (education ministry) machine-readable school-holiday file on data.public.lu.
- I did not check the licence or terms of OpenHolidays and Nager.Date in this pass (both are commonly described as open source and free; check before redistribution).

## 2. Sunday shop openings (ouvertures dominicales), Ville de Luxembourg

### Takeaway
**No machine-readable source exists.** None of the 19 Ville de Luxembourg datasets on data.public.lu covers Sunday openings, and searches for "dominical", "dimanche", "ouverture" and "commerces" return 0 results.

### Cited Findings
- The organisation `ville-de-luxembourg` has 19 datasets (Veloh, air quality, AVL buses, parkings, playgrounds, population, fountains, etc.), none on Sunday openings — [VdL datasets API](https://data.public.lu/api/1/organizations/ville-de-luxembourg/datasets/?page_size=50)
- `https://www.vdl.lu/fr/vivre/commerce/ouvertures-dominicales` → **404**, and `https://www.luxembourg-city.com/fr/shopping/ouvertures-dominicales` → **404** (both guessed URLs).

### Inferences
- The only option would be scraping an HTML page or a yearly PDF/communiqué. That breaks the "factual-only / stable" rule, so do not add a source for it.

### Gaps
- I did not find the current official HTML page that lists Sunday openings, so I could not check it.

## 3. Recycling centres

### Takeaway
Primary: the INSPIRE GML from Géoportail (26 recycling-centre points, CC0, refreshed 2026-11-05). There is no maintained CSV or GeoJSON. The backup is an old 2018 shapefile from the Administration de l'environnement. SuperDrecksKëscht and Valorlux have no open dataset (0 hits).

### Cited Findings
- **PRIMARY GML**: `https://data.public.lu/fr/datasets/r/be8c3b2e-88d3-4ddb-955c-40b354123d29` → `200 application/octet-stream 34772`. `gml:FeatureCollection` with namespace `us-emf` 4.0, **26** `<us-emf:EnvironmentalManagementFacility>`. Fields: `gml:description` = name (e.g. "Centre de Differdange", "Centre de SIDEC", "Centre de Ville de Luxembourg"), `base:localId` = `rc.1`…`rc.26`, `gml:pos` in **EPSG:3035** (e.g. `2944398.67 4025463.27`; axis order northing/easting must be checked during reprojection), `us-emf:status`. Licence **cc-zero**, org Géoportail — [dataset 5e5920e3f176a15ca239e617](https://data.public.lu/api/1/datasets/5e5920e3f176a15ca239e617/)
- A WMS GetCapabilities endpoint exists for the same data (`https://wms.inspire.geoportail.lu/geoserver/us/wms?...`), but it serves map images, not useful as data — same dataset.
- **BACKUP, outdated**: `recycling-centers.shp.zip` (2018 data, uploaded 2020-02-14), resource `99ca8915-e0db-4409-a598-3e0184c311ca`. The other resources are annual PDF/DOCX reports. Org "Administration de l'environnement", **cc-zero** — [dataset 584995f6cc765e71ba15394c](https://data.public.lu/api/1/datasets/584995f6cc765e71ba15394c/). (I did not download the SHP. Parsing a shapefile needs a dependency outside the allowed list.)
- Related, untested: VdL "Récipients publics pour la collecte séparée" (public separate-collection bins) appears in the Ville de Luxembourg dataset list — [VdL datasets](https://data.public.lu/api/1/organizations/ville-de-luxembourg/datasets/?page_size=50)

### Inferences
- The GML can be parsed with `xml.etree` from the standard library, with no new dependency. Only the EPSG:3035 → WGS84 conversion is needed: it can be done in DuckDB spatial, or the points can be kept in 3035.
- An OSM Overpass query (`amenity=recycling` + `recycling_type=centre`) is a likely backup, but I did not test it.

### Gaps
- I found no SuperDrecksKëscht or Valorlux machine-readable list, and no opening hours.

## 4. AED defibrillators

### Takeaway
**There is no official dataset on data.public.lu** (0 hits for "defibrillateur", "defibrillator", "DAE", "AED"). OpenStreetMap through Overpass is the only verified source: 295 objects in the LU bounding box. The main overpass-api.de instance was saturated (502) during the test, but the `maps.mail.ru` mirror answered.

### Cited Findings
- **PRIMARY (de facto), Overpass**: POST `data=[out:json][timeout:90];nwr["emergency"="defibrillator"](49.44,5.73,50.19,6.54);out center tags;`
  - `https://overpass-api.de/api/interpreter` → **502** "server at capacity" (on 2026-11-24). Without a User-Agent it gives **406**, so a UA must be sent.
  - `https://maps.mail.ru/osm/tools/overpass/api/interpreter` → `200 application/json 61734`, **295 elements**. Example: `{"type":"node","id":2192633166,"lat":49.7708843,"lon":5.9844138,"tags":{"emergency":"defibrillator","indoor":"yes","defibrillator:location":"Aussen","opening_hours":"24/7"}}`. Most common tags: `indoor` (174), `defibrillator:location` (96), `access` (91), `opening_hours` (36), `operator` (21), `name` (only 8).
  - Licence: OSM **ODbL** (attribution and share-alike) — [OSM copyright](https://www.openstreetmap.org/copyright)
- The bounding box includes parts of BE, FR and DE. Filter with `area["ISO3166-1"="LU"][admin_level=2]` (this query timed out on the saturated instance) or with a point-in-polygon check on the LU border.
- Not AED, but nearby: CGDIS "Rettungspunkte" (forest rescue points, licence **odc-odbl**) — [dataset 5eec6f76d2bfb251e132f1ba](https://data.public.lu/api/1/datasets/5eec6f76d2bfb251e132f1ba/). VdL "Points de sauvetage" (rescue points) — [VdL datasets](https://data.public.lu/api/1/organizations/ville-de-luxembourg/datasets/?page_size=50). I did not test the content of either.

### Inferences
- Plan for at least two Overpass mirrors with retry/backoff. The public Overpass instances are not an SLA service.
- Coverage is clearly incomplete (295 objects, only 8 with a `name`), so describe it as "crowd-sourced, not exhaustive".

### Gaps
- I found no official registry (CGDIS / Ministère de la Santé / "Fondation Cœur").

## 5. LU-Alert and weather warnings

### Takeaway
LU-Alert publishes every alert as a **CAP 1.2 XML** file (profile `cap-lu:1.0`) on data.public.lu (CC-BY, about 907 resources, one file per alert). Weather vigilance: the MeteoAlarm JSON feed for LU works (CAP as JSON). The MeteoLux CSV on data.public.lu works but is empty when there is no warning. The MeteoLux API `/metweb/warnings` needs `lat` and `long`.

### Cited Findings
- **PRIMARY LU-Alert**: dataset "Alertes du système LU-ALERT", org LU-Alert, licence **cc-by**, frequency continuous, 907 resources (XML + PDF), latest 2026-11-20. There is **no stable "latest" URL**: list the resources through `https://data.public.lu/api/1/datasets/67aca67bcaea3ae62308114f/`, sort by `last_modified`, and fetch the `.xml` files you have not seen yet — [dataset API](https://data.public.lu/api/1/datasets/67aca67bcaea3ae62308114f/)
  - Example: `https://data.public.lu/fr/datasets/r/8bc441c6-3494-42ac-a3f0-4b843a2f6630` → `200 text/xml 38106`. `<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2:profile:cap-lu:1.0">` with `identifier` (`LU-Alert.1795186733.4876.0`), `sent`, `status`=Actual, `msgType`=Alert, `scope`=Public, `code`=IN_ZONE, then `<info>` repeated per language (`language` fr-FR…) with `category` (Health), `event` ("Avertissement alimentaire"), `urgency`, `severity`, `certainty`, `eventCode/value` (`FOOD_WARNING`), `effective`, `expires`, `headline`, `description` (**escaped HTML**: it must be stripped or ignored under factual-only).
- **PRIMARY weather vigilance, MeteoAlarm JSON**: `https://feeds.meteoalarm.org/api/v1/warnings/feeds-luxembourg` → `200 application/json 74910`, 11 warnings on 2026-11-24. Structure: `{"warnings":[{"alert":{identifier,incidents,info[],msgType,references,scope,sender,sent,status}}]}`. In `info[]`: `category:["Met"]`, `severity` (Minor…), `urgency`, `certainty`, `effective`, `onset`, `expires`, `headline` ("Rain warning"), `senderName:"MeteoLux"`, `parameter:[{"valueName":"awareness_type","value":"10; Rain"},{"valueName":"awareness_level","value":"1; green; Minor"}]`, `area:[{"areaDesc":"Luxembourg-North","polygon":[…]}]`. Licence: per the Atom feed, "terms equivalent to CC BY 4.0, with additional requirements for redistributing" — [MeteoAlarm feed](https://feeds.meteoalarm.org/api/v1/warnings/feeds-luxembourg)
  - Atom: `https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-luxembourg` → `200 application/atom+xml 989` (empty feed at test time, only the header) — [Atom](https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-luxembourg)
- **BACKUP, MeteoLux CSV (data.public.lu, cc-zero, continuous)**: `https://data.public.lu/fr/datasets/r/9291c76d-26cd-4bc2-98cd-6c214595ed38` → `200 text/csv 126`. Line 1 `sep=;`, line 2 `created;24-11-2026 13:55:41`, line 3 header `NORTH;SOUTH;LEGEND;DESCRIPTION;VALUE;COLOR;ICON;LINK;START_VALIDITY_DATE;END_VALIDITY_DATE`, no rows when there is no warning. FR/DE/EN versions: `878bae1b-…`, `c13e4827-…`, `5e41bef8-…` — [dataset 5746f18e32cc220d498879b8](https://data.public.lu/api/1/datasets/5746f18e32cc220d498879b8/)
- MeteoLux API (`https://metapi.ana.lu/api/v1`, CC0, OpenAPI at `/api/v1/openapi.json` → 200): `GET /metweb/warnings?lat=49.61&long=6.13&lang=fr` → `200 application/json`, `[]` (no active warning). Without lat/long or `city` (integer) it returns 422. Other routes: `/hvd/observations`, `/hvd/stations`, `/metweb/today?canton=…` — [MeteoLux API dataset](https://data.public.lu/api/1/datasets/6a5096faf69cd5b32f884ce9/)
- Municipal: Esch-sur-Alzette RSS `https://esch.lu/feed/alert` (cc-zero, hourly) — [dataset 619533b0fa018077eaf662eb](https://data.public.lu/api/1/datasets/619533b0fa018077eaf662eb/) (not tested with curl).

### Inferences
- LU-Alert is append-only by design: one file per alert, which fits the incremental "zero deletion" ingestion rule well. MeteoAlarm's `awareness_level` gives the colour code without parsing free text.

### Gaps
- I did not find a direct JSON/RSS feed on lu-alert.lu (not explored).

## 6. Public petitions (Chamber of Deputies)

### Takeaway
Official dataset from the Chamber of Deputies (CC0) in CSV/XML/XLSX, 3,545 petitions, **but it has not been updated since 2025-03-28** (latest filing 2025-03-12). Usable for history only. No live API found on petitiounen.lu.

### Cited Findings
- **PRIMARY, CSV**: `https://data.public.lu/fr/datasets/r/6c43ab5c-8fc2-493b-822a-35793ac1c840` → `200 text/csv 3631978`. UTF-8 with BOM, comma-separated. Columns: `PETITION_NBR,FILING_DATE(dd/mm/yyyy),OFFICIAL_TITLE,TYPE(PUB|ORD),STATUS,ASSOCIATION_ROLE,ASSOCIATION_NAME,RESIDENCY_COUNTRY,GOAL,SIGN_NBR_ELECTRONIC,SIGN_NBR_PAPER,MOTIVATION`. 3,545 rows, 2006-07-18 → 2025-03-12. STATUS values: CLOTUREE 1682, IRRECEVABLE 1084, RECLASSEE 319, RECEVABLE 99, SEUIL_NON_ATTEINT 93, SEUIL_ATTEINT 75, … Licence **cc-zero**, org "Chambre des Députés du Grand-Duché de Luxembourg" — [dataset 633dc0be73184376cf400d5f](https://data.public.lu/api/1/datasets/633dc0be73184376cf400d5f/)
- **BACKUP (same content), XML**: `https://data.public.lu/fr/datasets/r/1a7d42d2-34ac-4765-9d57-385e521f95ec` → `200 application/xml 4547253`. XLSX `d2c4dc95-…`, ZIP `8a703b66-…` — same dataset.
- Under factual-only, `GOAL` and `MOTIVATION` are editorial text and must be blocked. `ASSOCIATION_NAME/ROLE` may count as PII; check before use.
- The other CHD datasets (deputies, votes, parliamentary questions) were updated 2026-11-24, but the petitions one was not — [CHD datasets](https://data.public.lu/api/1/organizations/627e56d3a9bc6b2dd946a3ea/datasets/?page_size=50)
- `https://www.petitiounen.lu/` → 200 HTML. No `/api/`, JSON or RSS link found in the page.

### Gaps
- No live source for 2025-2026 petitions. Ask the Chamber of Deputies about the update cadence.

## 7. Unemployment (ADEM and STATEC)

### Takeaway
Primary: ADEM "Chiffres-clés" on data.public.lu (CC0, monthly, updated 2026-11-20), with **job seekers by municipality and sex, monthly since 2012-01**. Backup: LUSTAT SDMX `DF_B3010` (monthly national) and `DF_X026` (annual by canton/municipality, with unemployment rate).

### Cited Findings
- **PRIMARY by municipality**: `https://data.public.lu/fr/datasets/r/7bc964ea-7744-4860-ae84-24cc0ef3777d` → `200 text/csv 1900268`. Header `Date,Commune,Canton,Sexe,Personnes`, values quoted, e.g. `"31-08-2026","Mertzig","Diekirch","Femmes","26"`. Date is end of month in `dd-mm-yyyy`. 36,186 rows, 2012-01 → 2026-10, 103 municipalities (pre-merger names may vary), Sexe ∈ {Femmes, Hommes}. **Rows are not sorted.** Org ADEM, **cc-zero**, monthly — [dataset 5e538be8f176a1373747c0f2](https://data.public.lu/api/1/datasets/5e538be8f176a1373747c0f2/)
- Other resources in the same dataset (all CSV, 2026-11-20): `de-flux.csv` `f425b0e3-…` (`Date,Residence,Ouvertures,Clotures`), `de-age-duree.csv` `a41b3377-…` (`Date,Age,Duree_inscription,Personnes`, since 2006), profiles `6074ffe2-…`, by occupation `2114333b-…`, nationality `2b3ca540-…`, non-residents `76660a32-…`, benefit recipients `bf01e691-…`, job offers `82415dc2-…`/`eb98a7a3-…`. Definitions PDF `a407c5bc-…` — same dataset.
- **BACKUP, monthly national**: `https://lustat.statec.lu/rest/data/LU1,DF_B3010,1.0/all?startPeriod=2026-01&dimensionAtObservation=AllDimensions` with header `Accept: application/vnd.sdmx.data+csv;version=1.0.0` → `200 application/vnd.sdmx.data+csv 6021`. Columns `DATAFLOW,FREQ,SPECIFICATION,TIME_PERIOD,OBS_VALUE,…`. SPECIFICATION C01…C10 (`C09` = "Number of unemployed", `C10` = active population). Latest period 2026-10. `DF_B3019` = seasonally adjusted with unemployment rate (not queried) — [LUSTAT dataflows](https://lustat.statec.lu/rest/dataflow/all/all/latest)
- **BACKUP, by municipality (annual)**: `https://lustat.statec.lu/rest/data/LU1,DF_X026,1.1/all?lastNObservations=1&dimensionAtObservation=AllDimensions` → `200 … 38151` (691 rows, year 2025). VARIABLE C1 employed, C2 wage-earners, C3 non-wage-earners, **C4 unemployed**, C5 active population, **C6 unemployment rate (%)**. SPECIFICATION = `LU`, `CT01..CT12` (cantons), `CMxxxxx` (municipalities). `startPeriod=2026-01` → 404 `NoRecordsFound` (annual data) — [codelists](https://lustat.statec.lu/rest/dataflow/LU1/DF_X026/1.1?references=all)

### Inferences
- The ADEM file covers all 12 cantons and has 14+ years of monthly history. It meets the "12 cantons + maximum history" rule better than LUSTAT.

### Gaps
- I did not check the LUSTAT licence or terms in this pass (STATEC publishes under CC0 on data.public.lu, but I did not verify the SDMX API terms).

## 8. Inflation (STATEC IPCN) as a backup to Eurostat HICP

### Takeaway
LUSTAT SDMX works without a key and returns SDMX-CSV. `DSD_PRIX_CONSO@DF_E5100` = headline IPCN (base 1948=100, monthly, latest 2026-10). `DSD_ECOICOP_PRIX@DF_E5405` = IPCN by ECOICOP v2 (base 2025=100). HICP is also on LUSTAT (`DF_E5404`).

### Cited Findings
- **IPCN headline**: `https://lustat.statec.lu/rest/data/LU1,DSD_PRIX_CONSO@DF_E5100,1.0/all?startPeriod=2026-01&dimensionAtObservation=AllDimensions` (Accept `application/vnd.sdmx.data+csv;version=1.0.0`) → `200 … 1261`. Many `_Z` dimension columns, then `TIME_PERIOD,OBS_VALUE`, e.g. `2026-01,1022.3` … `2026-10,1064.42`, MEASURE=IPCN, UNIT=IND, BASE_PERIOD=1948 — [LUSTAT](https://lustat.statec.lu/rest/dataflow/all/all/latest)
- **IPCN detail**: `…/LU1,DSD_ECOICOP_PRIX@DF_E5405,1.0/all?startPeriod=2026-08…` → `200 … 170420`. Columns `DATAFLOW,UNIT_MEASURE,MEASURE,FREQ,ECOICOP_1999,BASE_PERIOD,ECOICOP_2018,TIME_PERIOD,OBS_VALUE,…`, e.g. `IPCN,M,_Z,2025,CP0833,2026-10,96.48` — same source.
- Other flows found: E5400/E5404 HICP (ECOICOP v1/v2), E5401 IPCN v1, E5408/E5409 special aggregates, E5101 6-month moving average of the IPCN (used for wage indexation) — [dataflow list](https://lustat.statec.lu/rest/dataflow/all/all/latest)

### Gaps
- I did not find a direct total code (TOTAL/CP00) in E5405 among the first rows. Filter by ECOICOP_2018 code (not checked).

## 9. Housing: Observatoire de l'Habitat

### Takeaway
All files are XLS (OLE2) or XLSX, CC0, org "Ministère du Logement – Observatoire de l'Habitat", updated 2026-09-24 (semi-annual or quarterly). **No CSV.** The legacy `.xls` format needs a reader such as `xlrd`, which is not in the allowed dependencies. DuckDB's `excel` extension reads only `.xlsx`. Prefer the XLSX resources.

### Cited Findings
- Advertised sale prices, national series (quarterly): current euros `https://data.public.lu/fr/datasets/r/a732f754-4a67-4d4c-928d-0c293b23565b` → `200 application/vnd.ms-excel 134656` (**XLS**, magic `d0cf11e0`). Constant euros `d9cfa7bf-f423-4d92-ba54-17450472b385` — [dataset 57f25796cc765e231b285e95](https://data.public.lu/api/1/datasets/57f25796cc765e231b285e95/)
- Advertised rents, national series (quarterly): current euros `5aae0e80-5c79-4f98-b95b-937c3c968ca9`, constant euros `240708e8-d49f-4247-99ad-e91f95d0ad31` (XLS) — [dataset 57f259c7111e9b0c14235a96](https://data.public.lu/api/1/datasets/57f259c7111e9b0c14235a96/)
- **Prices by municipality (semi-annual)**: apartments, last 12 months `50299491-6363-4f5e-bb3b-d8db82c400fe` → `200 vnd.ms-excel 74240` (XLS). Houses, last 12 months `411d7b8d-893a-4541-8973-e09889937645` (XLS). **Apartment series by municipality 2010+** `https://data.public.lu/fr/datasets/r/1d20f982-57e1-4ae2-a278-dc78c88c21dc` → `200 octet-stream 254265` (**XLSX**, magic `PK`, updated 2026-03-26). **House series 2010-2025** `14b0156e-ff87-4a36-a867-933fc9a6f903` (XLSX) — [dataset 57f254fb111e9b0c14235a94](https://data.public.lu/api/1/datasets/57f254fb111e9b0c14235a94/)
- Rents by municipality: apartments, 12 months `fb6616ef-a4c6-44ea-bf0c-74de9a81ab68` → `200 vnd.ms-excel 75264` (XLS). Houses `e1e5485b-8a2e-4593-b1ea-226eb9299f0d` (XLS). Apartment series `94e4a229-c564-4dd2-99b5-6b6e9d29eafd` (XLS) — [dataset 57f25c07cc765e23279433af](https://data.public.lu/api/1/datasets/57f25c07cc765e23279433af/)
- Luxembourg-Ville by district (XLSX): apartments `https://data.public.lu/fr/datasets/r/c11d6f9d-2efe-417a-8e52-a5a98dc635f0` → `200 octet-stream 44180` (PK). Houses `4a3de498-…`. Apartment series `b63bc110-…`, house series `f5febcd9-…` — [dataset 57f26313111e9b0c089eefc3](https://data.public.lu/api/1/datasets/57f26313111e9b0c089eefc3/)
- Transaction prices (notarial deeds): "Le Logement en Chiffres" exists **only as PDF** (no. 20, September 2026) — [dataset 57f2651e111e9b0c2c8d6386](https://data.public.lu/api/1/datasets/57f2651e111e9b0c2c8d6386/)
- Private alternative: ChatHome "Prix annoncés des logements par commune" (advertised prices by municipality), **cc-by**, monthly, 18 resources, 2026-10-25 — [dataset 6ad5d6bac89cc30fccb2553a](https://data.public.lu/api/1/datasets/6ad5d6bac89cc30fccb2553a/) (content not tested).

### Inferences
- The XLSX series by municipality (2010+) are the best fit for "maximum history + municipality granularity", but they are updated only once a year (March). The "last 12 months" files are XLS and would need a non-allowed dependency, or an ADR.

### Gaps
- I did not inspect the internal layout of the XLSX files (sheets, header rows) in this pass. A parser will need this check.
- STATEC LUSTAT probably has housing price indices (not searched, out of scope).
