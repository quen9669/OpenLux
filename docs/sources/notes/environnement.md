# Sources ouvertes Luxembourg vérifiées — Environnement (tests live du 2026-11-24)

All URLs below were tested with `curl.exe` on 2026-11-24 (~20:00–21:00 UTC) unless marked UNVERIFIED / FAILED. "HTTP 200 + type + bytes" is the observed result. "features.geoportail.lu" is an OGC API – Features (pygeoapi) server: `/collections/{id}/items?f=json&limit=N` (GeoJSON, WGS84 lon/lat, `numberMatched`, paging via `limit`/`offset`; `f=csv` alternative advertised in `links`).

## Q0. Existing `config/sources.toml` URLs in this domain are fake (important for the writer)

### Takeaway
Every data.public.lu "slug-style" URL currently in `config/sources.toml` for these domains returns 404; data.public.lu stable links use resource UUIDs, never slugs.

### Cited Findings
- 404 text/html: `https://data.public.lu/fr/datasets/r/niveaux-eau-inondations.json`, `.../r/qualite-de-lair-temps-reel.json`, `.../r/surveillance-radiologique-luxembourg.json`, `.../r/eaux-de-baignade-luxembourg.csv`, `.../r/noise-zones-luxembourg.json`, `.../r/pollen-luxembourg.json` — tested live (curl).
- `https://eau.geoportail.lu/wfs/bathing_water.csv` → 404; `https://env.geoportail.lu/wfs/strategic_noise_maps` → connection failure (000, host does not resolve/answer); `https://inondations.lu/api/v1/water-levels` → 200 but **text/html** (website page, not an API) — tested live.
- Correct stable form verified: `https://data.public.lu/fr/datasets/r/<resource-uuid>` redirects to the latest file (e.g. `r/0e03052d-0506-481d-8fd8-98d670103204` → 200 application/json; `r/94fecbb1-4fce-4bee-8f2d-fc03b9fa314f` → 200 text/csv) — [data.public.lu API](https://data.public.lu/api/1/datasets/niveau-deau/).

### Inferences
- These 9 entries must be replaced, not just retried; they will never return data.

### Gaps
- None.

## Q1. Water levels / flood (niveaux d'eau, crues)

### Takeaway
Primary: AGE/CTIE CSV export from inondations.public.lu (42 stations, 15‑min, rolling 7 days, CC0). Backup: German PEGELONLINE REST API for the Moselle at Trier (no key, JSON); LU station metadata via data.public.lu GeoJSON / features.geoportail.lu collection 655.

### Cited Findings
- Dataset `niveau-deau`, org Administration de la gestion de l'eau, licence **cc-zero**, frequency daily — [data.public.lu API](https://data.public.lu/api/1/datasets/niveau-deau/).
- **PRIMARY** `https://inondations.public.lu/dam-assets/ctie/datas/Water-Levels-LocalTime.csv` (stable alias `https://data.public.lu/fr/datasets/r/94fecbb1-4fce-4bee-8f2d-fc03b9fa314f`) → 200 text/csv 221 627 B; `last-modified: Tue, 24 Nov 2026 20:46:37 GMT`, `Cache-Control: max-age=14400` (Cloudflare) — [file](https://inondations.public.lu/dam-assets/ctie/datas/Water-Levels-LocalTime.csv).
  - Format: **wide CSV**, quoted, UTF‑8. Header: `"Name","Number","Unit","17.11.2026 21:45",...,"24.11.2026 21:30"` (675 columns = 3 + 672 timestamps = 7 days × 96 quarter-hours). One row per station (42 rows), e.g. `SN_Remich,"",cm,339.0,337.0,...`. Timestamps `DD.MM.YYYY HH:MM` **local time (Europe/Luxembourg)**; empty strings for missing values; `Number` column empty; unit mostly `cm`, but **`Esch-Sure` is in `m`** (reservoir level).
  - Stations: SN_Remich, SN_Stadtbredimus, SN_Grevenmacher, SN_Wasserbillig, Perl, Gemünd_Our, Esch-Sure, Mondorf-les-bains, Ubersyren, Roodt sur Syre, Welscheid, Heiderscheidergrund, Welscheid-Village, Walferdange, Eischen, Livange, Bissen, Diekirch, Vianden, Kautenbach, Bollendorf, Rosport, Hesperange, Niederfeulen, Pfaffenthal, Pétange, Michelau, Clervaux, Troisvierges, Wiltz, Müllerthal, Steinsel, Ettelbrück / Wark, Ettelbrück / Alzette, Larochette, Schoenfels, Hunnebuer, Mersch, Reichlange, Dasbourg, Bigonville, Mertert.
- Transposed variant `https://inondations.public.lu/dam-assets/ctie/datas/Water-Levels-Localstation.csv` (resource `d96ab196-70c0-4ae9-86d5-9e9e8c4bd1dc`) → 200 text/csv 221 419 B; header row = station names, rows `Number`, `Unit`, then one row per timestamp (long-ish, easier to parse) — [file](https://inondations.public.lu/dam-assets/ctie/datas/Water-Levels-Localstation.csv).
- Discharge files guessed (`Discharge-LocalTime.csv`, `Water-Levels-UTC.csv`, …) → 404 — tested live; no discharge export found.
- Station coordinates: `https://download.data.public.lu/resources/niveau-deau/20261111-020305/wasserstand.geojson` (resource `5835f0e0-2e30-4a1f-b3a5-f05fba878de9`, stable `https://data.public.lu/fr/datasets/r/5835f0e0-2e30-4a1f-b3a5-f05fba878de9`) → 200 application/geo+json 27 940 B; FeatureCollection, Point WGS84 `[lon, lat]`, properties `OBJECTID`, `Nom` (e.g. "Eischen"), `Etat_de_se` ("En service"), `Hyperlinks_graph` (`https://inondations.public.lu/fr/graph/107.html`). Same via `https://features.geoportail.lu/collections/655/items?f=json` (numberMatched 51) — [features.geoportail.lu](https://features.geoportail.lu/collections/655/items?f=json&limit=2).
- **BACKUP** PEGELONLINE (WSV, Germany): `https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations.json?waters=MOSEL` → 200 JSON list (`uuid`, `number`, `shortname`, `longname`, `km`, `agency`, `longitude`, `latitude`, `water`); station TRIER UP uuid `3bec53ca-444e-4014-a7b0-07b3591e954b` (km 195.3, 49.732, 6.627). Measurements: `https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/3bec53ca-444e-4014-a7b0-07b3591e954b/W/measurements.json?start=P1D` → 200 JSON array `[{"timestamp":"2026-11-23T22:00:00+01:00","value":311.0}, ...]` (cm, 15 min) — [PEGELONLINE](https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations.json?waters=MOSEL). `waters=SAUER` → `[]` (no Sûre stations). Licence: PEGELONLINE states DL-DE/Zero-2.0 on its site (not re-checked in this session).

### Inferences
- Rolling 7-day window only → history must be accumulated by OpenLux itself (fits the "zero suppression" incremental rule): poll at least every few days; Cloudflare cache means ≤4 h freshness at best.
- Parse with stdlib `csv`; melt wide → long (station, ts_local, value, unit); convert local → UTC with `zoneinfo`.
- PEGELONLINE only covers the German Moselle (Trier is downstream of LU border); it is a degraded backup, not a 12-canton substitute.

### Gaps
- No discharge (débit) or flood-alert-level machine-readable feed found; flood alert thresholds not in the CSV.
- Long historical archive of LU water levels not found as open data (only the 7-day rolling export).
- Groundwater `niveau-de-la-nappe-alluviale` dataset contains station geometry only (geojson 8 357 B), not measurements.

## Q2. Radioactivity / ambient gamma dose rate

### Takeaway
No working open machine-readable source of Luxembourg gamma dose-rate VALUES was found. Only the EURDEP station list (14 LU probes, coordinates) is openly reachable; the value endpoints are not public.

### Cited Findings
- data.public.lu searches `radioactivite`, `radiologique`, `gamma`, `dose`, `radioprotection`, `radiation`, `radioactivity`, `telerad`, `nucleaire` → 0 datasets — [data.public.lu API](https://data.public.lu/api/1/datasets/?q=gamma&page_size=8).
- `https://remap.jrc.ec.europa.eu/api/maps/` → 200 application/json 335 738 B: array of 6 259 stations `{"lat":49.63,"lng":6.19,"cnt":"LU","code":"LU0227"}`; 14 LU codes: LU0227, LU21216, LU21118, LU21057, LU21117, LU21324, LU21322, LU21323, LU21321, LU21326, LU21325, LU21219, LU21059, LU21320 — [JRC REMAP](https://remap.jrc.ec.europa.eu/api/maps/). **No values, no licence statement.**
- Value endpoints referenced in the REMAP page JS (`/app/map/simple/api/timeseries/v1/stations/daily/timeseries?codes=`, `/api/stations/{code}`, `/api/timeseries/v1/stations/timeseries/{start}/{end}`) all → 404 when called directly; the JS config shows `mapSvc/api/auth/login`, i.e. an authenticated backend — [REMAP Advanced](https://remap.jrc.ec.europa.eu/Advanced.aspx). `https://eurdep.jrc.ec.europa.eu/` is an EU Login single-sign-on page.
- BfS open WFS (`https://www.imis.bfs.de/ogc/opendata/ows`) exposes only German ODL layers (`opendata:odlinfo_odl_1h_latest`, `opendata:odlinfo_timeseries_odl_1h`, …); `opendata:eurdep_latestValue` → "Feature type unknown" — tested live.
- Radon (not gamma dose rate, but radiological): `https://features.geoportail.lu/collections/1468/items?f=json` → 200, per-commune radon polygons with `radon_luref_all_Project_COMMUNE`, `..._CANTON`, `F2023_carte_radon_csv_Activite2022` (Bq/m³), `..._Nbre_mes2022`, `..._Act_max2022` — static, all 12 cantons — [features.geoportail.lu](https://features.geoportail.lu/collections/1468/items?f=json&limit=1).

### Inferences
- Mark `radioactivity` source NOT_TESTED/unavailable rather than inventing a URL. Radon per commune (collection 1468) is a credible static substitute for a "radiological" table.

### Gaps
- No public EURDEP/LU Division de la radioprotection API for live dose rate; would need EURDEP data-exchange access (authentication) — not tested further.

## Q3. Bathing water quality (eaux de baignade)

### Takeaway
Primary: AGE raw analyses XLSX (2009-04-15 → 2025-09-30, CC0, annual). Backup/current status: OGC API collections 656 (sites + current "Baignade" status) and 581 (quality class per site).

### Cited Findings
- Dataset `raw-data-of-bathing-water-analyses-in-luxembourg`, AGE, **cc-zero**, frequency annual, temporal coverage 2009-04-15 → 2025-09-30; parameters intestinal enterococci, E. coli, turbidity (Directive 2006/7/EC) — [data.public.lu API](https://data.public.lu/api/1/datasets/raw-data-of-bathing-water-analyses-in-luxembourg/).
- **PRIMARY** `https://download.data.public.lu/resources/raw-data-of-bathing-water-analyses-in-luxembourg/20260713-123203/bathing-water-lu.xlsx` → 200 application/octet-stream 418 515 B; single sheet, range A1:P5734 (~5 733 rows, long format). Headers (German): `Probenahmenummer`, `Stationsnummer` (e.g. L112010A03-1), `Stationsname` (Liefrange, Lultzhausen, "Weiswampach, vir beim Steg"…), `Oberflächengewässer (Name|Nummer)` ("Sûre|1.16."), `Parametertypname` ("Escherichia coli", "Entérocoques intestinaux", "Turbidité", "Aspect de l'échantillon"…), `Vorzeichen` ("<"), `Wert`, `Datum` (Excel serial, e.g. 39925 = 2009-04-23), `Einheitensymbol` (FNU, …), `Nachweisgrenze`, `Analysemethode (Kurzname/Name)`, then LUREF X/Y and lat/lon columns (e.g. 59203, 107861, 49.90472, 5.87862) — file inspected live. Stable link: resource UUID not captured (use data.public.lu API `resources[0].url`).
- **BACKUP** `https://features.geoportail.lu/collections/656/items?f=json` → 200, 15 features, properties `NAME` ("Lac Weiswampach Zone 2"), `Baignade` ("hors saison"), `Hyperlinks` (profile PDF), Point WGS84 — [collection 656](https://features.geoportail.lu/collections/656/items?f=json&limit=1).
- `https://features.geoportail.lu/collections/581/items?f=json` → 200, 15 features, properties `messstationen_GISADMIN_Badegewaesser_OBJECTID`, `wasserrahmenrichtlinie_GISADMIN_Badegewaesser_Ergebnisse_RESULT` ("excellente") — [collection 581](https://features.geoportail.lu/collections/581/items?f=json&limit=2).
- Static GeoJSON on data.public.lu (`age_bathing_waters.geojson`, `age_quality_of_bathing_water.geojson`) dated 2018-03 — stale.

### Inferences
- XLSX parsing needs a stdlib zip+XML reader (no openpyxl allowed by AGENTS.md) or DuckDB's `excel`/spatial extension; flag as a parser cost. Only 3 sites groups (Upper Sûre reservoir, Remerschen, Weiswampach) → not 12-canton coverage by nature.

### Gaps
- EEA bathing-water API not tested (tool budget).

## Q4. Pollen

### Takeaway
Primary (live/forecast): Open-Meteo air-quality API pollen variables (CAMS model, no key, history back to at least 2022). Backup (measured, historical): Geoportail INSPIRE daily pollen data (33 taxa since 1992-01-01, CC0) via WFS JSON or a 356 MB GML file.

### Cited Findings
- **PRIMARY** `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=49.6117,50.0544&longitude=6.1319,6.0294&hourly=birch_pollen,grass_pollen,alder_pollen,mugwort_pollen,olive_pollen,ragweed_pollen&past_days=1&forecast_days=1&timezone=Europe/Luxembourg` → 200 application/json 5 176 B; multi-location request returns a **JSON array** of objects `{latitude, longitude, utc_offset_seconds, timezone, elevation, hourly_units:{birch_pollen:"grains/m³",...}, hourly:{time:["2026-11-23T00:00",...], birch_pollen:[...], ...}}` — [Open-Meteo](https://air-quality-api.open-meteo.com/v1/air-quality?latitude=49.6117&longitude=6.1319&hourly=birch_pollen,grass_pollen&start_date=2026-05-01&end_date=2026-05-01).
  - Seasonal values verified: 2026-05-01 08–13h grass 3.1→2.3, birch 9.4→3.8 grains/m³; `start_date=2022-08-01` also returns values (grass 3.5, 1.6 …). Single location → object, multi → array.
- Dataset `inspire-annex-iii-theme-human-health-daily-pollen-concentration-data`, org Géoportail, **cc-zero**: "Daily pollen concentration data for 33 pollen types since Jan 1, 1992 in Luxembourg" — [data.public.lu API](https://data.public.lu/api/1/datasets/inspire-annex-iii-theme-human-health-daily-pollen-concentration-data/).
  - GML file `https://download.data.public.lu/resources/inspire-annex-iii-theme-human-health-daily-pollen-concentration-data/20261116-154157/hh.envhealthdeterminantmeasure-pollen.gml` (356 356 098 B, last_modified 2026-11-16): INSPIRE HH 5.0, EPSG:3035, one `hh:EnvHealthDeterminantMeasure` per day×taxon, `gml:id="19920101_Ambrosia_0"`, `<gml:description>… 0 pollens/m3 of Ambrosia`, `hh:measureTime/gml:beginPosition` — head inspected via HTTP Range.
  - **BACKUP** WFS: `https://wms.inspire.geoportail.lu/geoserver/hh/wfs?service=WFS&version=2.0.0&request=GetFeature&outputFormat=application/json&typeNames=hh:HH.EnvHealthDeterminantMeasure_Pollen_betula&count=2` → 200 application/json; each feature = one day, properties `date` ("2014-10-04T00:00:00Z"), `station` ("pollen_1"), and all 33 taxa as **strings** (`ambrosia`, `artemisia`, `alnus`, `betula`, `gramineae`, `quercus`, `urtica`, …); geometry EPSG:3035 (one station). `totalFeatures` 9 069; `sortBy=date DESC` latest = **2018-03-16** — [Geoportail INSPIRE WFS](https://wms.inspire.geoportail.lu/geoserver/hh/wfs?service=WFS&version=2.0.0&request=GetCapabilities).
- pollen.lu: not tested for a machine-readable feed (no API found on data.public.lu; dataset `pollen` by PolnPy is from 2018, licence notspecified).

### Inferences
- Open-Meteo is model data (CAMS Europe), not measurements; MeteoLux/LIST station data are measured but the WFS appears frozen at 2018 — the GML might be more recent (file refreshed 2026-11-16) but its last measurement date was not verified.
- Open-Meteo licence: CC-BY 4.0 per Open-Meteo terms (attribution required) — from prior knowledge, not re-verified here.

### Gaps
- Most recent date in the 356 MB GML not verified (unordered file; full download not done).
- Open-Meteo olive/ragweed/mugwort values not checked in-season.

## Q5. Noise zones / strategic noise maps

### Takeaway
Primary: OGC API Features collections on features.geoportail.lu (GeoJSON polygons with `lden`/`lngt` classes per source: roads, rail, airport, multi-exposure). Backup: data.public.lu GeoPackages (DF4_8 2021 submission, CC0, quinquennial).

### Cited Findings
- Dataset `environmental-noise-strategic-noise-maps`, Administration de l'environnement, **cc-zero**, quinquennial; GPKG resources e.g. `1f3914d8-6708-4b39-9aa6-4a94fb0db62b` "Strategic noise maps (DF4_8 submission) for major roads 2021", `5ab6c129-…` railways 2021, `17293fe1-…` airport 2021, `ca939cba-…` agglomeration 2021 (download URLs under `https://download.data.public.lu/resources/environmental-noise-strategic-noise-maps/20250724-…/`); documentation zips for 2011/2016/2021/2023 — [data.public.lu API](https://data.public.lu/api/1/datasets/environmental-noise-strategic-noise-maps/). (GPKG files themselves not downloaded.)
- **PRIMARY** `https://features.geoportail.lu/collections/3258/items?f=json&limit=1` ("Cartographie du Bruit concernant les routes principales (LDEN)") → 200 application/json; properties `lden` (80.0), `objectid`, `st_area(shape)`, `st_perimeter(shape)`; Polygon WGS84 — [collection 3258](https://features.geoportail.lu/collections/3258/items?f=json&limit=1).
- `https://features.geoportail.lu/collections/3010/items?f=json&limit=1` ("Grand aéroport 2023 (Lden)") → 200; properties `name` ("35.0"), `stufe` (1), `objectid`; large polygons (70 KB per feature) — [collection 3010](https://features.geoportail.lu/collections/3010/items?f=json&limit=1).
- Other relevant collection ids (titles from `https://features.geoportail.lu/collections?f=json`, not individually fetched): 3257 roads LNGT, 3256/3255 rail LDEN/LNGT, 157 airport LDEN, 3011 airport 2023 Lngt, 3260/3259 major roads 2021 Lden/Lngt, 2761/2762 main railways 2021, 2768/2767 agglomeration roads 2021, 2769/2770 industry 2021, 3041/3042 multi-exposure 2021, 2839/2840 priority noise-management zones 2021, 1642 road noise hotspots, 3039/3040 quiet areas 2024 — [collections list](https://features.geoportail.lu/collections?f=json).

### Inferences
- Polygons are very heavy (fine-grained raster-derived); for a Gold table aggregate to area per `lden` band per commune/canton with DuckDB spatial, or store only attributes + area.

### Gaps
- Whether the 2023 airport / 2021 road layers are the latest round (2026 round not seen).

## Q6. Weather observations (MeteoLux) and air quality (real-time)

### Takeaway
Weather: MeteoLux API `metapi.ana.lu` is live, keyless, CC0 (Findel HVD observations + Dudelange tower 10‑min series). Air quality: the AEV "réseau télémétrique" OGC collection is reachable but **stale since 2025-12-13**; the only verified live source is Open-Meteo (CAMS model). EEA up-to-date CSVs returned 502.

### Cited Findings
- Dataset `meteolux-api`, MeteoLux, **cc-zero**, continuous; OpenAPI `https://metapi.ana.lu/api/v1/openapi.json` (200, "MeteoLux API backend 1.21.4 - prod") lists `/hvd/observations`, `/hvd/stations`, `/hvd/observations/metadata`, `/metweb/obs/findel`, `/metweb/obs/dudelange`, `/metweb/warnings`, `/metweb/metar/{icao}`, `/metweb/today`… — [MeteoLux API docs](https://metapi.ana.lu/api/v1/docs).
- **PRIMARY weather** `https://metapi.ana.lu/api/v1/hvd/observations` → 200 application/json: `{"licence":["Creative Commons","https://creativecommons.org/public-domain/cc0/"],"docUrl":"/docs","data":[{"id":"st","value":-2.3}, {"id":"su","value":75}, {"id":"sqnh","value":1017.1}, {"id":"srr","value":0.0}, {"id":"s2ff_rwymd0","value":6.2}, …],"totalItemCount":27,"timestamp":"2026-11-24T20:03:00Z"}` (ids: st air temp °C, std dew point, su RH %, sqnh/sqfe/spsl pressure hPa, srr precip, s2dd/s2ff wind dir/speed per runway, svv visibility) — single station ELLX — [endpoint](https://metapi.ana.lu/api/v1/hvd/observations).
- `https://metapi.ana.lu/api/v1/hvd/stations` → one station: `LUX0000001`, ICAO ELLX, WMO 06590, location [6.23301, 49.63258], masl 376.12, validFrom 1947-01-01 — [endpoint](https://metapi.ana.lu/api/v1/hvd/stations).
- `https://metapi.ana.lu/api/v1/metweb/obs/dudelange` → 200 JSON 33 776 B: array `{date:"2026-11-23", timeInterval:"20:51-21:00", direction100M, averageForceKmh100M, humidity100M, temperature50M/100M/150M}` (~24 h of 10‑min rows) — [endpoint](https://metapi.ana.lu/api/v1/metweb/obs/dudelange).
- **BACKUP weather** same data as file: `https://data.public.lu/fr/datasets/r/0e03052d-0506-481d-8fd8-98d670103204` (dataset `hvd-annex-3-meteorological-live-weather-observations-at-luxembourg-airport-ellx`, CC0) → 200 application/json 2 169 B, identical structure, timestamp 2026-11-24T20:03:00Z — [data.public.lu](https://data.public.lu/api/1/datasets/hvd-annex-3-meteorological-live-weather-observations-at-luxembourg-airport-ellx/). Open-Meteo forecast API (already in config) remains the 12-canton gridded option.
- Air quality AEV: `https://features.geoportail.lu/collections/1357/items?f=json&limit=100` ("Réseau télémétrique") → 200, 8 stations (TES11/TEG12 Esch, TBK11 Oberpallen, TVI11 Vianden, TBW11 Beidweiler, TLB11/TLG11/TLW11 Luxembourg), properties `code`, `adr_city`, `luref_x/luref_y` (LUREF EPSG:2169), `ozone_value`, `pm10_value`, `no2_value` (µg/m³), `index`, `*_index`, `date_str` **"13/12/2025 14:00"** → not updated for ~11 months — [collection 1357](https://features.geoportail.lu/collections/1357/items?f=json&limit=1).
- INSPIRE AQ telemetric WFS `https://wms.inspire.geoportail.lu/geoserver/hh/wfs?...typeNames=hh:HH.EnvHealthDeterminantMeasure_AQTelemetric_no2` → 200 JSON, 85 618 hourly features, properties `date`, `aqd_station_id` (STA-LU0101A…0112A, 9 stations), `no2`, `o3`, `pm10`, `pm2_5`, `so2`, `co`, `no`, `c6h6` (strings, -999 = missing), EPSG:3035; latest `date` = **2018-12-31T23:00Z** (historical only, 2018) — [WFS caps](https://wms.inspire.geoportail.lu/geoserver/hh/wfs?service=WFS&version=2.0.0&request=GetCapabilities).
- **PRIMARY air quality (live, modelled)** `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=49.6117&longitude=6.1319&current=european_aqi,pm10,pm2_5,nitrogen_dioxide,ozone` → 200: `{"current_units":{"european_aqi":"EAQI","pm10":"μg/m³",...},"current":{"time":"2026-11-24T20:00","interval":3600,"european_aqi":34,"pm10":11.2,"pm2_5":9.4,"nitrogen_dioxide":20.4,"ozone":33.0}}` — [Open-Meteo](https://air-quality-api.open-meteo.com/v1/air-quality?latitude=49.6117&longitude=6.1319&current=european_aqi,pm10,pm2_5,nitrogen_dioxide,ozone).
- FAILED: `https://discomap.eea.europa.eu/map/fme/latest/LU_NO2.csv`, `LU_PM10.csv`, `LU_O3.csv` → 502 Bad Gateway (twice) — UNVERIFIED, may be transient.

### Inferences
- For measured AQ, collection 1357 can be kept as a *backup* but the pipeline must compare `date_str` to now and flag staleness (last_changed_utc logic) instead of treating it as fresh.
- MeteoLux HVD has no history endpoint → accumulate snapshots (every run) to build history.

### Gaps
- No verified live, measured, open AQ feed for Luxembourg today (EEA 502; OpenAQ requires an API key — not tested).
- MeteoLux secondary stations beyond ELLX/Dudelange not exposed in HVD API.
