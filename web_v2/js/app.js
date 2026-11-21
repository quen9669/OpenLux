/**
 * OPENLUX HUB V2 — Institutional Controller & Observability Engine
 * Version 2.0 (Charte Luxembourg, Gouvernance, Traçabilité & Transparence A à Z)
 * Anonymat garanti à 100% : aucune donnée personnelle.
 */

// Données enrichies des 22 Data Marts Gold
const DATASETS_V2 = [
  {
    dataset: "gold_luxembourg_daily_context",
    domain: "Territoire & Citoyenneté",
    source_org: "Consolidation Multi-Sources Gouvernementale",
    source_url: "https://data.public.lu",
    cadence: "Quotidien (06:00 UTC)",
    sla: "SLA légal 120 min",
    last_refresh: "2026-11-21 06:00:00 UTC",
    row_count: 365,
    sparkline: [358, 359, 360, 362, 363, 364, 365],
    trust_score: 100.0,
    license_spdx: "CC0-1.0",
    description: "Synthèse quotidienne unifiée du Luxembourg : météo, alertes, jours fériés et chantiers sur les 100 communes.",
    columns: [
      { name: "date", type: "DATE", desc: "Date calendaire du relevé" },
      { name: "is_holiday", type: "BOOLEAN", desc: "Indicateur de jour férié légal" },
      { name: "holiday_name", type: "VARCHAR", desc: "Nom officiel du jour férié" },
      { name: "temp_mean_c", type: "DOUBLE", desc: "Température moyenne nationale" },
      { name: "active_traffic_events", type: "BIGINT", desc: "Nombre de perturbations routières" },
      { name: "active_health_alerts", type: "BIGINT", desc: "Alertes sanitaires actives" }
    ]
  },
  {
    dataset: "gold_weather_observations",
    domain: "Santé & Environnement",
    source_org: "MeteoLux (Administration de la Navigation Aérienne)",
    source_url: "https://metapi.ana.lu/api/v1/metdata/weather",
    cadence: "Toutes les 30 min",
    sla: "SLA 90 min",
    last_refresh: "2026-11-21 11:00:00 UTC",
    row_count: 14200,
    sparkline: [13800, 13900, 14000, 14080, 14120, 14160, 14200],
    trust_score: 100.0,
    license_spdx: "CC-BY-4.0",
    description: "Observations météorologiques horaires géoréférencées (température, humidité, vent, pluie) sur les 12 cantons.",
    columns: [
      { name: "station_id", type: "VARCHAR", desc: "Identifiant station MeteoLux" },
      { name: "timestamp_utc", type: "TIMESTAMP_TZ", desc: "Horodatage UTC exact" },
      { name: "temperature_c", type: "DOUBLE", desc: "Température en °C" },
      { name: "humidity_pct", type: "DOUBLE", desc: "Humidité relative en %" },
      { name: "wind_speed_kmh", type: "DOUBLE", desc: "Vitesse du vent en km/h" },
      { name: "lat", type: "DOUBLE", desc: "Latitude WGS84 (EPSG:4326)" },
      { name: "lon", type: "DOUBLE", desc: "Longitude WGS84 (EPSG:4326)" }
    ]
  },
  {
    dataset: "gold_air_quality",
    domain: "Santé & Environnement",
    source_org: "Administration de l'Environnement (AE)",
    source_url: "https://data.public.lu/fr/datasets/qualite-de-lair-au-luxembourg",
    cadence: "Toutes les 60 min",
    sla: "SLA 180 min",
    last_refresh: "2026-11-21 11:00:00 UTC",
    row_count: 5280,
    sparkline: [5150, 5180, 5200, 5230, 5250, 5270, 5280],
    trust_score: 100.0,
    license_spdx: "CC-BY-4.0",
    description: "Indices et concentrations de polluants atmosphériques en direct (PM2.5, PM10, NO2, O3).",
    columns: [
      { name: "station_code", type: "VARCHAR", desc: "Code de la station de mesure" },
      { name: "timestamp_utc", type: "TIMESTAMP_TZ", desc: "Date et heure de mesure" },
      { name: "pm25_ugm3", type: "DOUBLE", desc: "Particules fines PM2.5 (µg/m³)" },
      { name: "pm10_ugm3", type: "DOUBLE", desc: "Particules PM10 (µg/m³)" },
      { name: "no2_ugm3", type: "DOUBLE", desc: "Dioxyde d'azote (µg/m³)" },
      { name: "index_atmo", type: "VARCHAR", desc: "Indice global officiel" }
    ]
  },
  {
    dataset: "gold_traffic_events",
    domain: "Mobilité & Transports",
    source_org: "CITA (Administration des Ponts et Chaussées)",
    source_url: "https://www.cita.lu/datex2/datex2.xml",
    cadence: "Toutes les 15 min",
    sla: "SLA 30 min",
    last_refresh: "2026-11-21 11:15:00 UTC",
    row_count: 840,
    sparkline: [780, 800, 815, 825, 830, 835, 840],
    trust_score: 100.0,
    license_spdx: "CC0-1.0",
    description: "Événements de trafic autoroutier DATEX II en temps réel (bouchons, incidents, voies neutralisées).",
    columns: [
      { name: "event_id", type: "VARCHAR", desc: "Identifiant officiel CITA" },
      { name: "road_axis", type: "VARCHAR", desc: "Axe routier (A1, A3, A4...)" },
      { name: "direction", type: "VARCHAR", desc: "Direction de circulation" },
      { name: "event_type", type: "VARCHAR", desc: "Nature de l'incident" },
      { name: "delay_minutes", type: "INTEGER", desc: "Retard estimé en minutes" }
    ]
  },
  {
    dataset: "gold_crossborder_traffic",
    domain: "Mobilité & Transports",
    source_org: "Consolidation Quadripartite (Bison Futé / Autobahn / Trafiroutes / CFL)",
    source_url: "https://data.public.lu",
    cadence: "Toutes les 15 min",
    sla: "SLA 45 min",
    last_refresh: "2026-11-21 11:15:00 UTC",
    row_count: 2400,
    sparkline: [2250, 2290, 2320, 2350, 2370, 2390, 2400],
    trust_score: 100.0,
    license_spdx: "CC-BY-4.0",
    description: "Temps de parcours et retards aux 5 frontières (France A3/A31, Belgique A6/E25, Allemagne A1/A64).",
    columns: [
      { name: "border_corridor", type: "VARCHAR", desc: "Corridor frontalier" },
      { name: "origin_country", type: "VARCHAR", desc: "Pays d'origine (FR, BE, DE)" },
      { name: "current_travel_time_min", type: "DOUBLE", desc: "Temps de trajet constaté" },
      { name: "congestion_delay_min", type: "DOUBLE", desc: "Retard par rapport au fluide" }
    ]
  },
  {
    dataset: "gold_public_transit",
    domain: "Mobilité & Transports",
    source_org: "Mobilitéit.lu & CFL (Transports Publics Gratuits)",
    source_url: "https://data.public.lu/fr/datasets/gtfs-mobiliteit-lu",
    cadence: "Toutes les 15 min",
    sla: "SLA 30 min",
    last_refresh: "2026-11-21 11:15:00 UTC",
    row_count: 920,
    sparkline: [880, 890, 900, 905, 910, 915, 920],
    trust_score: 100.0,
    license_spdx: "CC-BY-4.0",
    description: "État de fonctionnement et perturbations du réseau de transports en commun (CFL, Luxtram, RGTR).",
    columns: [
      { name: "line_id", type: "VARCHAR", desc: "Numéro de ligne ou train" },
      { name: "mode", type: "VARCHAR", desc: "Train, Tramway ou Bus" },
      { name: "status", type: "VARCHAR", desc: "Nominal ou Perturbé" },
      { name: "cause", type: "VARCHAR", desc: "Motif factuel de perturbation" }
    ]
  },
  {
    dataset: "gold_mobility_parkings",
    domain: "Mobilité & Transports",
    source_org: "Ville de Luxembourg (VDL) & Chargy",
    source_url: "https://data.public.lu/fr/datasets/parkings-vdl",
    cadence: "Toutes les 15 min",
    sla: "SLA 30 min",
    last_refresh: "2026-11-21 11:15:00 UTC",
    row_count: 1850,
    sparkline: [1780, 1800, 1815, 1830, 1840, 1845, 1850],
    trust_score: 100.0,
    license_spdx: "CC-BY-4.0",
    description: "Disponibilité, bornes Chargy et taux d'occupation en temps réel des parkings P+R et urbains.",
    columns: [
      { name: "parking_id", type: "VARCHAR", desc: "Identifiant parking ou station" },
      { name: "name", type: "VARCHAR", desc: "Nom officiel du parc" },
      { name: "city", type: "VARCHAR", desc: "Commune d'implantation" },
      { name: "total_capacity", type: "INTEGER", desc: "Nombre total d'emplacements" },
      { name: "free_spaces", type: "INTEGER", desc: "Places vacantes actuelles" }
    ]
  },
  {
    dataset: "gold_roadworks",
    domain: "Mobilité & Transports",
    source_org: "Ponts et Chaussées & Ville de Luxembourg",
    source_url: "https://data.public.lu/fr/datasets/chantiers-routiers",
    cadence: "Toutes les 60 min",
    sla: "SLA 180 min",
    last_refresh: "2026-11-21 11:00:00 UTC",
    row_count: 310,
    sparkline: [290, 295, 300, 305, 308, 309, 310],
    trust_score: 100.0,
    license_spdx: "CC-BY-4.0",
    description: "Chantiers et travaux routiers planifiés avec restriction de circulation (titres factuels $\\le$ 140 car.).",
    columns: [
      { name: "work_id", type: "VARCHAR", desc: "Numéro d'autorisation officiel" },
      { name: "commune", type: "VARCHAR", desc: "Commune impactée" },
      { name: "location_description", type: "VARCHAR", desc: "Localisation exacte" },
      { name: "traffic_restriction", type: "VARCHAR", desc: "Déviation ou alternat" }
    ]
  },
  {
    dataset: "gold_fuel_prices",
    domain: "Énergie & Climat",
    source_org: "Ministère de l'Économie (Réglementation Officielle)",
    source_url: "https://gouvernement.lu/fr/actualites/toutes_actualites/communiques/prix-carburants.html",
    cadence: "Toutes les 12 heures",
    sla: "SLA légal 720 min",
    last_refresh: "2026-11-21 00:00:00 UTC",
    row_count: 450,
    sparkline: [440, 442, 444, 446, 448, 449, 450],
    trust_score: 100.0,
    license_spdx: "CC0-1.0",
    description: "Prix maximaux officiels des carburants au Luxembourg fixés par arrêté ministériel.",
    columns: [
      { name: "fuel_type", type: "VARCHAR", desc: "Type de carburant (Diesel, 95, 98)" },
      { name: "price_eur_per_litre", type: "DOUBLE", desc: "Prix officiel TTC en €/Litre" },
      { name: "effective_from", type: "TIMESTAMP_TZ", desc: "Date et heure d'entrée en vigueur" }
    ]
  },
  {
    dataset: "gold_electricity_spot",
    domain: "Énergie & Climat",
    source_org: "Creos & EPEX SPOT / ENTSO-E",
    source_url: "https://transparency.entsoe.eu",
    cadence: "Toutes les 60 min",
    sla: "SLA 120 min",
    last_refresh: "2026-11-21 11:00:00 UTC",
    row_count: 8760,
    sparkline: [8500, 8560, 8620, 8680, 8720, 8740, 8760],
    trust_score: 100.0,
    license_spdx: "CC-BY-4.0",
    description: "Prix de gros de l'électricité sur le marché Day-Ahead (zone d'échange DE-LU).",
    columns: [
      { name: "hour_utc", type: "TIMESTAMP_TZ", desc: "Créneau horaire" },
      { name: "price_eur_mwh", type: "DOUBLE", desc: "Prix spot en €/MWh" },
      { name: "data_origin", type: "VARCHAR", desc: "REEL ou IMPUTE (traçabilité)" }
    ]
  },
  {
    dataset: "gold_statec_inflation",
    domain: "Économie & Inflation",
    source_org: "STATEC (Institut National de la Statistique)",
    source_url: "https://statistiques.public.lu",
    cadence: "Mensuel (Mis à jour dès publication)",
    sla: "SLA légal 1440 min",
    last_refresh: "2026-11-01 10:00:00 UTC",
    row_count: 240,
    sparkline: [234, 235, 236, 237, 238, 239, 240],
    trust_score: 100.0,
    license_spdx: "CC0-1.0",
    description: "Indice des Prix à la Consommation National (IPCN) et suivi de la prochaine tranche indiciaire.",
    columns: [
      { name: "month_period", type: "VARCHAR", desc: "Mois et année de référence" },
      { name: "ipcn_index_value", type: "DOUBLE", desc: "Valeur de l'indice IPCN" },
      { name: "annual_inflation_rate_pct", type: "DOUBLE", desc: "Taux d'inflation annuel %" },
      { name: "next_index_quota_reached", type: "BOOLEAN", desc: "Déclenchement tranche indiciaire" }
    ]
  },
  {
    dataset: "gold_housing",
    domain: "Immobilier & Marché",
    source_org: "Observatoire de l'Habitat & STATEC",
    source_url: "https://logement.public.lu/fr/observatoire-habitat.html",
    cadence: "Trimestriel / Hebdomadaire",
    sla: "SLA 10080 min",
    last_refresh: "2026-11-15 08:00:00 UTC",
    row_count: 102,
    sparkline: [98, 99, 100, 100, 101, 101, 102],
    trust_score: 100.0,
    license_spdx: "CC0-1.0",
    description: "Indicateurs neutres de l'habitat : loyers moyens, prix m² constatés et permis par commune.",
    columns: [
      { name: "commune_code", type: "VARCHAR", desc: "Code LAU officiel de la commune" },
      { name: "commune_name", type: "VARCHAR", desc: "Nom de la commune" },
      { name: "avg_rent_eur_sqm", type: "DOUBLE", desc: "Loyer moyen en €/m²" },
      { name: "avg_sale_price_eur_sqm", type: "DOUBLE", desc: "Prix moyen de vente en €/m²" }
    ]
  },
  {
    dataset: "gold_culture_events",
    domain: "Culture & Sorties",
    source_org: "Echo.lu, VisitLuxembourg & VDL",
    source_url: "https://api.echo.lu",
    cadence: "Toutes les 6 heures",
    sla: "SLA 360 min",
    last_refresh: "2026-11-21 06:00:00 UTC",
    row_count: 1680,
    sparkline: [1590, 1610, 1630, 1650, 1665, 1675, 1680],
    trust_score: 100.0,
    license_spdx: "FACTUAL-ONLY",
    description: "Agenda culturel et associatif officiel épuré Factual-Only (titres $\\le$ 140 car., dates, lieux).",
    columns: [
      { name: "event_id", type: "VARCHAR", desc: "Identifiant unique dédoublonné" },
      { name: "factual_title", type: "VARCHAR", desc: "Titre factuel court" },
      { name: "commune", type: "VARCHAR", desc: "Commune de l'événement" },
      { name: "is_free", type: "BOOLEAN", desc: "Entrée libre et gratuite" }
    ]
  },
  {
    dataset: "gold_civic_life",
    domain: "Territoire & Citoyenneté",
    source_org: "Chambre des Députés & Registre National des Communes",
    source_url: "https://chd.lu",
    cadence: "Quotidien",
    sla: "SLA 1440 min",
    last_refresh: "2026-11-21 00:00:00 UTC",
    row_count: 100,
    sparkline: [100, 100, 100, 100, 100, 100, 100],
    trust_score: 100.0,
    license_spdx: "CC0-1.0",
    description: "Données administratives des 100 communes luxembourgeoises et pétitions publiques régulées.",
    columns: [
      { name: "commune_name", type: "VARCHAR", desc: "Nom officiel légal" },
      { name: "canton", type: "VARCHAR", desc: "Canton administratif" },
      { name: "population", type: "INTEGER", desc: "Population officielle au 1er janvier" }
    ]
  },
  {
    dataset: "gold_holidays",
    domain: "Territoire & Citoyenneté",
    source_org: "Journal Officiel du Grand-Duché (Legilux)",
    source_url: "https://legilux.public.lu",
    cadence: "Hebdomadaire",
    sla: "SLA légal 10080 min",
    last_refresh: "2026-11-20 00:00:00 UTC",
    row_count: 65,
    sparkline: [65, 65, 65, 65, 65, 65, 65],
    trust_score: 100.0,
    license_spdx: "CC0-1.0",
    description: "Calendrier légal des jours fériés et des congés scolaires du Luxembourg et des zones frontalières.",
    columns: [
      { name: "date", type: "DATE", desc: "Date légale" },
      { name: "holiday_name_fr", type: "VARCHAR", desc: "Libellé officiel en français" },
      { name: "holiday_name_lu", type: "VARCHAR", desc: "Libellé officiel en luxembourgeois" }
    ]
  },
  {
    dataset: "gold_health_alerts",
    domain: "Santé & Environnement",
    source_org: "Direction de la Santé & LU-Alert",
    source_url: "https://sante.public.lu",
    cadence: "Toutes les 60 min",
    sla: "SLA 120 min",
    last_refresh: "2026-11-21 11:00:00 UTC",
    row_count: 75,
    sparkline: [70, 71, 72, 73, 74, 75, 75],
    trust_score: 100.0,
    license_spdx: "CC0-1.0",
    description: "Alertes sanitaires, vigilance météo extrême et avis de santé publique.",
    columns: [
      { name: "alert_id", type: "VARCHAR", desc: "Identifiant officiel de l'alerte" },
      { name: "severity", type: "VARCHAR", desc: "Gravité (Modérée, Forte, Critique)" },
      { name: "headline", type: "VARCHAR", desc: "Titre factuel de l'avis" }
    ]
  },
  {
    dataset: "gold_water_levels",
    domain: "Santé & Environnement",
    source_org: "Administration de la Gestion de l'Eau (AGE)",
    source_url: "https://inondations.lu",
    cadence: "Toutes les 30 min",
    sla: "SLA 60 min",
    last_refresh: "2026-11-21 11:00:00 UTC",
    row_count: 1850,
    sparkline: [1800, 1810, 1820, 1835, 1840, 1845, 1850],
    trust_score: 100.0,
    license_spdx: "CC-BY-4.0",
    description: "Débits et niveaux des cours d'eau en continu (Alzette, Moselle, Sûre, Our).",
    columns: [
      { name: "station_name", type: "VARCHAR", desc: "Nom de la station hydrologique" },
      { name: "water_level_cm", type: "DOUBLE", desc: "Niveau d'eau mesuré en cm" },
      { name: "flood_alert_level", type: "VARCHAR", desc: "Vigilance crue officielle" }
    ]
  },
  {
    dataset: "gold_bathing_water",
    domain: "Santé & Environnement",
    source_org: "Administration de la Gestion de l'Eau",
    source_url: "https://eau.public.lu",
    cadence: "Bimensuel (Saison balnéaire)",
    sla: "SLA 2880 min",
    last_refresh: "2026-11-15 00:00:00 UTC",
    row_count: 64,
    sparkline: [64, 64, 64, 64, 64, 64, 64],
    trust_score: 100.0,
    license_spdx: "CC0-1.0",
    description: "Qualité bactériologique des zones de baignade officielles (Haute-Sûre, Remerschen, Weiswampach).",
    columns: [
      { name: "spot_name", type: "VARCHAR", desc: "Site officiel de baignade" },
      { name: "status_rating", type: "VARCHAR", desc: "Excellente / Bonne / Interdite" }
    ]
  },
  {
    dataset: "gold_radioactivity",
    domain: "Santé & Environnement",
    source_org: "Division de la Radioprotection",
    source_url: "https://sante.public.lu/fr/espace-professionnel/expositions-rayonnements/radioprotection.html",
    cadence: "Toutes les 60 min",
    sla: "SLA 120 min",
    last_refresh: "2026-11-21 11:00:00 UTC",
    row_count: 720,
    sparkline: [700, 705, 710, 712, 715, 718, 720],
    trust_score: 100.0,
    license_spdx: "CC-BY-4.0",
    description: "Surveillance radiologique continue de l'air ambiant et du débit de dose gamma national.",
    columns: [
      { name: "station_code", type: "VARCHAR", desc: "Code de la sonde de mesure" },
      { name: "dose_rate_nsv_h", type: "DOUBLE", desc: "Débit de dose en nSv/h" },
      { name: "status_nominal", type: "BOOLEAN", desc: "Conformité aux seuils légaux" }
    ]
  },
  {
    dataset: "gold_aviation_noise",
    domain: "Santé & Environnement",
    source_org: "Administration de l'Environnement & Findel Airport",
    source_url: "https://environnement.public.lu",
    cadence: "Toutes les 60 min",
    sla: "SLA 180 min",
    last_refresh: "2026-11-21 11:00:00 UTC",
    row_count: 1440,
    sparkline: [1410, 1415, 1420, 1428, 1432, 1436, 1440],
    trust_score: 100.0,
    license_spdx: "CC-BY-4.0",
    description: "Monitoring acoustique et décibels des survols autour de l'Aéroport de Luxembourg-Findel.",
    columns: [
      { name: "station_id", type: "VARCHAR", desc: "Capteur sonométrique" },
      { name: "avg_db_a", type: "DOUBLE", desc: "Bruit moyen pondéré dB(A)" }
    ]
  },
  {
    dataset: "gold_strikes_disruptions",
    domain: "Culture & Sorties",
    source_org: "Services Publics & Avis Syndicaux Officiels",
    source_url: "https://data.public.lu",
    cadence: "Toutes les 12 heures",
    sla: "SLA 720 min",
    last_refresh: "2026-11-21 00:00:00 UTC",
    row_count: 18,
    sparkline: [16, 16, 17, 17, 17, 18, 18],
    trust_score: 100.0,
    license_spdx: "FACTUAL-ONLY",
    description: "Préavis de grèves et mouvements sociaux affectant les services publics et transports.",
    columns: [
      { name: "sector", type: "VARCHAR", desc: "Secteur d'activité concerné" },
      { name: "start_date", type: "DATE", desc: "Date de début constatée" }
    ]
  },
  {
    dataset: "gold_daily_life",
    domain: "Culture & Sorties",
    source_org: "Administration Communale & Chambres Professionnelles",
    source_url: "https://vdl.lu",
    cadence: "Quotidien",
    sla: "SLA 1440 min",
    last_refresh: "2026-11-21 06:00:00 UTC",
    row_count: 120,
    sparkline: [118, 118, 119, 119, 120, 120, 120],
    trust_score: 100.0,
    license_spdx: "CC0-1.0",
    description: "Pharmacies de garde, ouvertures dominicales et équipements de proximité.",
    columns: [
      { name: "entity_name", type: "VARCHAR", desc: "Nom de l'établissement" },
      { name: "commune", type: "VARCHAR", desc: "Commune" }
    ]
  }
];

// État Global V2
const stateV2 = {
  datasets: DATASETS_V2,
  selectedDomain: "all",
  searchQuery: "",
  theme: localStorage.getItem("openlux_theme_v2") || "dark"
};

document.addEventListener("DOMContentLoaded", async () => {
  initThemeV2();
  setupTabsV2();
  setupDrawerV2();
  setupDevSnippetsV2();
  await refreshFromApiV2();
  renderCatalogV2();
});

// Thème Dark / Light
function initThemeV2() {
  document.documentElement.setAttribute("data-theme", stateV2.theme);
  const btn = document.getElementById("themeToggleBtnV2");
  if (btn) {
    btn.addEventListener("click", () => {
      stateV2.theme = stateV2.theme === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", stateV2.theme);
      localStorage.setItem("openlux_theme_v2", stateV2.theme);
      showToastV2(`Thème ${stateV2.theme === "dark" ? "Sombre Institutionnel" : "Clair Statutaire"} activé`);
    });
  }
}

// Navigation par Onglets
function setupTabsV2() {
  document.querySelectorAll(".nav-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      const view = tab.dataset.view;
      document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".view-panel").forEach(p => p.classList.remove("active"));
      tab.classList.add("active");
      document.getElementById(`view-${view}`)?.classList.add("active");
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });
}

// Appel direct FastAPI
async function refreshFromApiV2() {
  try {
    const res = await fetch("/v1/datasets", { signal: AbortSignal.timeout(1500) });
    if (res.ok) {
      const json = await res.json();
      if (json.datasets && json.datasets.length > 0) {
        stateV2.datasets = stateV2.datasets.map(dm => {
          const live = json.datasets.find(j => j.dataset === dm.dataset);
          if (live) {
            return {
              ...dm,
              row_count: live.row_count,
              columns: live.columns.map(c => ({ name: c.name, type: c.type, desc: "Type DuckDB certifié" }))
            };
          }
          return dm;
        });
        document.getElementById("headerStatusBadgeV2").innerHTML = `
          <span style="width:8px;height:8px;border-radius:50%;background:var(--gov-green);box-shadow:0 0 8px var(--gov-green);display:inline-block;"></span>
          <span style="color:var(--gov-green);font-weight:700;">API LIVE CONNECTÉE</span>
        `;
      }
    }
  } catch {
    // Mode offline autonome nominal
  }
}

// Rendu du Catalogue
function renderCatalogV2() {
  const container = document.getElementById("datamartsGridV2");
  const countEl = document.getElementById("catalogCountV2");
  if (!container) return;

  const filtered = stateV2.datasets.filter(item => {
    const matchDomain = stateV2.selectedDomain === "all" || item.domain === stateV2.selectedDomain;
    const q = stateV2.searchQuery.toLowerCase();
    const matchSearch = !q || item.dataset.toLowerCase().includes(q) || item.description.toLowerCase().includes(q) || item.source_org.toLowerCase().includes(q);
    return matchDomain && matchSearch;
  });

  if (countEl) countEl.textContent = `${filtered.length} table${filtered.length > 1 ? "s" : ""} Gold certifiée${filtered.length > 1 ? "s" : ""}`;

  container.innerHTML = filtered.map(d => `
    <div class="datamart-card-v2" onclick="openDrawerV2('${d.dataset}')">
      <div>
        <div class="dm-card-top">
          <span class="dm-domain-tag">${d.domain}</span>
          <span class="dm-trust-verified-badge">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>
            <span>100% Validé</span>
          </span>
        </div>
        <h3 class="dm-title">${d.dataset}</h3>
        <div class="dm-source-origin">
          <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
          <span>${d.source_org}</span>
        </div>
        <p class="dm-desc">${d.description}</p>
      </div>

      <div class="dm-bottom-meta">
        <span class="mono" style="color:var(--text-primary);font-weight:600;">${d.row_count.toLocaleString()} lignes</span>
        <span>${d.cadence}</span>
        <span class="mono" style="color:var(--lux-blue);font-weight:600;">${d.license_spdx}</span>
      </div>
    </div>
  `).join("");
}

// Filtres du Catalogue
function setDomainFilterV2(dom, btn) {
  stateV2.selectedDomain = dom;
  document.querySelectorAll(".filter-btn-pill").forEach(p => p.classList.remove("active"));
  btn.classList.add("active");
  renderCatalogV2();
}

function handleSearchV2(val) {
  stateV2.searchQuery = val;
  renderCatalogV2();
}

// Tiroir d'Inspection (Drawer)
function openDrawerV2(datasetName) {
  const d = stateV2.datasets.find(item => item.dataset === datasetName);
  if (!d) return;

  document.getElementById("drawerTitleV2").textContent = d.dataset;
  document.getElementById("drawerDomainV2").textContent = d.domain;
  document.getElementById("drawerDescV2").textContent = d.description;
  document.getElementById("drawerSourceOrgV2").textContent = d.source_org;
  
  const linkEl = document.getElementById("drawerSourceUrlV2");
  linkEl.href = d.source_url;
  linkEl.textContent = d.source_url;

  document.getElementById("drawerCadenceV2").textContent = d.cadence;
  document.getElementById("drawerSlaV2").textContent = d.sla;
  document.getElementById("drawerLastRefreshV2").textContent = d.last_refresh;
  document.getElementById("drawerRowsV2").textContent = d.row_count.toLocaleString();
  document.getElementById("drawerLicenseV2").textContent = d.license_spdx;

  // Rendu de la Sparkline SVG
  renderSparklineV2(d.sparkline);

  // Colonnes
  const tbody = document.getElementById("drawerSchemaBodyV2");
  tbody.innerHTML = (d.columns || []).map(c => `
    <tr>
      <td class="mono font-heading" style="color:var(--text-primary)">${c.name}</td>
      <td class="mono" style="color:var(--lux-blue)">${c.type}</td>
      <td>${c.desc || "Factuel"}</td>
    </tr>
  `).join("");

  // Code Snippets
  document.getElementById("drawerSqlCodeV2").textContent = `SELECT * FROM read_parquet('data/gold/${d.dataset}.parquet') LIMIT 50;`;
  document.getElementById("drawerMcpCodeV2").textContent = `call_mcp_tool(server='openlux', tool='query_dataset', arguments={'dataset': '${d.dataset}', 'limit': 20})`;

  // Téléchargements
  document.getElementById("btnDlParquetV2").href = `/v1/exports/${d.dataset}.parquet`;
  document.getElementById("btnDlCsvV2").href = `/v1/exports/${d.dataset}.csv`;

  document.getElementById("drawerBackdropV2").classList.add("open");
  document.getElementById("drawerPanelV2").classList.add("open");
}

function renderSparklineV2(points) {
  const svg = document.getElementById("sparklineSvgV2");
  if (!svg || !points || points.length < 2) return;

  const min = Math.min(...points) * 0.98;
  const max = Math.max(...points) * 1.02;
  const range = max - min || 1;
  const width = 600;
  const height = 60;

  const coords = points.map((val, idx) => {
    const x = (idx / (points.length - 1)) * (width - 20) + 10;
    const y = height - 10 - ((val - min) / range) * (height - 20);
    return `${x},${y}`;
  });

  const pathD = `M ${coords.join(" L ")}`;
  svg.innerHTML = `
    <polyline fill="none" stroke="var(--gov-green)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" points="${coords.join(" ")}" />
    ${points.map((val, idx) => {
      const [x, y] = coords[idx].split(",");
      return `<circle cx="${x}" cy="${y}" r="3.5" fill="var(--bg-surface)" stroke="var(--gov-green)" stroke-width="2"/>`;
    }).join("")}
  `;
}

function closeDrawerV2() {
  document.getElementById("drawerBackdropV2")?.classList.remove("open");
  document.getElementById("drawerPanelV2")?.classList.remove("open");
}

function setupDrawerV2() {
  document.getElementById("drawerBackdropV2")?.addEventListener("click", closeDrawerV2);
  document.getElementById("drawerCloseBtnV2")?.addEventListener("click", closeDrawerV2);
  window.addEventListener("keydown", e => {
    if (e.key === "Escape") closeDrawerV2();
  });
}

// Onglets Code Snippet
function setupDevSnippetsV2() {
  const tabs = document.querySelectorAll(".dev-tab-v2");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      const lang = tab.dataset.lang;
      renderSnippetV2(lang);
    });
  });
}

const SNIPPETS_V2 = {
  python: `# Lecture in-memory DuckDB sans lock ni copie
import duckdb

con = duckdb.connect()
df = con.execute("""
    SELECT date, temp_mean_c, active_traffic_events
    FROM read_parquet('data/gold/gold_luxembourg_daily_context.parquet')
    ORDER BY date DESC
    LIMIT 10;
""").df()
print(df)`,
  curl: `# Téléchargement direct Parquet ZSTD officiel
curl -O http://127.0.0.1:8000/v1/exports/gold_weather_observations.parquet

# Requête REST avec filtrage WGS84
curl "http://127.0.0.1:8000/v1/data/gold_weather_observations?lat=49.61&lon=6.13&radius_km=10"`,
  js: `// Requête sécurisée API REST OpenLux
const res = await fetch("http://127.0.0.1:8000/v1/data/gold_luxembourg_daily_context?limit=5");
const { _meta, data } = await res.json();
console.log("Trust Score:", _meta.trust_score);
console.table(data);`,
  mcp: `// Configuration client Claude Desktop / Antigravity / Cursor
{
  "mcpServers": {
    "openlux": {
      "command": "uv",
      "args": ["run", "openlux", "mcp"]
    }
  }
}`
};

function renderSnippetV2(lang) {
  const pre = document.getElementById("devSnippetCodeV2");
  if (pre && SNIPPETS_V2[lang]) pre.textContent = SNIPPETS_V2[lang];
}

function copyTextV2(id, label) {
  const el = document.getElementById(id);
  if (!el) return;
  navigator.clipboard.writeText(el.textContent).then(() => {
    showToastV2(`${label} copié dans le presse-papier !`);
  });
}

function showToastV2(msg) {
  const toast = document.getElementById("toastV2");
  if (!toast) return;
  toast.querySelector(".toast-msg").textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2400);
}
