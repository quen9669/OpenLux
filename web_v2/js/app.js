/**
 * OPENLUX HUB V2 — Institutional Controller & Observability Engine
 * Version 2.0 (Charte Luxembourg, Gouvernance, Traçabilité & Transparence A à Z)
 * Anonymat garanti à 100% : aucune donnée personnelle.
 */

// Catalogue : aucune donnée codée en dur. Source = API /v1/datasets, sinon instantané
// data/catalog.json généré par le pipeline (mêmes chiffres mesurés).
async function loadCatalogV2() {
  for (const url of ["/v1/datasets", "data/catalog.json"]) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(4000) });
      if (!res.ok) continue;
      const json = await res.json();
      const list = Array.isArray(json) ? json : json.datasets;
      if (list && list.length) return { list, live: url.startsWith("/v1") };
    } catch {
      // essai suivant
    }
  }
  return { list: [], live: false };
}

function escapeHtmlV2(v) {
  const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  return String(v ?? "").replace(/[&<>"']/g, c => map[c]);
}

function sourceLabelV2(d) {
  return (d.sources || []).map(s => s.source_id).join(", ") || "—";
}

// État Global V2
const stateV2 = {
  datasets: [],
  selectedDomain: "all",
  searchQuery: "",
  monitoring: {
    sources: [],
    kpis: {},
    searchQuery: "",
    statusFilter: "all"
  },
  theme: localStorage.getItem("openlux_theme_v2") || "dark"
};

document.addEventListener("DOMContentLoaded", async () => {
  initThemeV2();
  setupTabsV2();
  setupDrawerV2();
  setupDevSnippetsV2();
  await refreshFromApiV2();
  await refreshMonitoringV2();
  renderDomainFiltersV2();
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

// Chargement du catalogue réel et chiffres clés
async function refreshFromApiV2() {
  const { list, live } = await loadCatalogV2();
  stateV2.datasets = list;
  const rows = list.reduce((acc, d) => acc + (d.row_count || 0), 0);
  const srcs = new Set(list.flatMap(d => (d.sources || []).map(s => s.source_id)));
  const setText = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
  setText("statTablesV2", list.length || "–");
  setText("statRowsV2", list.length ? `${rows.toLocaleString("fr-FR")} lignes en Parquet ZSTD` : "Catalogue indisponible");
  setText("statSourcesV2", srcs.size || "–");
  const badge = document.getElementById("headerStatusBadgeV2");
  if (badge) {
    const color = live ? "var(--gov-green)" : "var(--text-muted)";
    const label = live ? "API CONNECTÉE" : (list.length ? "INSTANTANÉ HORS LIGNE" : "AUCUNE DONNÉE");
    badge.innerHTML = `<span style="width:8px;height:8px;border-radius:50%;background:${color};display:inline-block;"></span><span style="color:${color};font-weight:700;">${label}</span>`;
  }
}

function renderDomainFiltersV2() {
  const box = document.getElementById("domainFiltersV2");
  if (!box) return;
  const domains = [...new Set(stateV2.datasets.map(d => d.domain))];
  box.innerHTML = `<button class="filter-btn-pill active" onclick="setDomainFilterV2('all', this)">Tous les domaines</button>` +
    domains.map(dm => `<button class="filter-btn-pill" onclick="setDomainFilterV2('${escapeHtmlV2(dm)}', this)">${escapeHtmlV2(dm)}</button>`).join("");
}

// Formatage du temps relatif
function formatRelativeTime(iso) {
  if (!iso) return "-";
  try {
    const diffSec = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
    if (diffSec < 60) return "À l'instant";
    if (diffSec < 3600) return `Il y a ${Math.floor(diffSec / 60)} min`;
    if (diffSec < 86400) return `Il y a ${Math.floor(diffSec / 3600)} h`;
    return `Il y a ${Math.floor(diffSec / 86400)} j`;
  } catch {
    return iso;
  }
}

// Appel direct FastAPI pour la Supervision des Flux
async function refreshMonitoringV2() {
  const btn = document.getElementById("btnRefreshMonitoringV2");
  if (btn) btn.classList.add("loading");
  try {
    const res = await fetch("/v1/status", { signal: AbortSignal.timeout(2500) });
    if (res.ok) {
      const data = await res.json();
      stateV2.monitoring.sources = data.sources || [];
      stateV2.monitoring.kpis = data.kpis || {};
      renderMonitoringKPIs(data);
      renderMonitoringV2();
      showToastV2("Supervision des flux actualisée en direct");
    }
  } catch (e) {
    console.warn("Mode monitoring hors-ligne ou API indisponible", e);
  } finally {
    if (btn) btn.classList.remove("loading");
  }
}

function renderMonitoringKPIs(data) {
  const kpis = data.kpis || {};
  const globalEl = document.getElementById("monKpiGlobalStatus");
  const detailEl = document.getElementById("monKpiGlobalDetail");
  const rowsEl = document.getElementById("monKpiTotalRows");
  const scoreEl = document.getElementById("monKpiAvgScore");
  const activeEl = document.getElementById("monKpiActiveFlows");
  const errEl = document.getElementById("monKpiAttentionErrors");

  if (globalEl) {
    const st = data.status || "HEALTHY";
    globalEl.textContent = st === "HEALTHY" ? "100% NOMINAL" : (st === "ATTENTION" ? "ATTENTION" : "DÉGRADÉ");
    globalEl.style.color = st === "HEALTHY" ? "var(--gov-green)" : (st === "ATTENTION" ? "var(--gov-warning)" : "var(--gov-danger)");
  }
  if (detailEl && kpis.total_sources) {
    detailEl.textContent = `${kpis.total_sources} flux sous contrôle SLA`;
  }
  if (rowsEl && kpis.total_rows_collected !== undefined) {
    rowsEl.textContent = kpis.total_rows_collected.toLocaleString();
  }
  if (scoreEl && kpis.average_trust_score !== undefined) {
    scoreEl.textContent = `${kpis.average_trust_score.toFixed(1)}%`;
  }
  if (activeEl && kpis.total_sources) {
    activeEl.textContent = `${kpis.healthy_count || 0} / ${kpis.total_sources}`;
  }
  if (errEl) {
    errEl.textContent = `${kpis.attention_count || 0} en dégradation • ${kpis.error_count || 0} en erreur`;
  }
}

function handleMonitoringSearchV2(q) {
  stateV2.monitoring.searchQuery = q.trim().toLowerCase();
  renderMonitoringV2();
}

function handleMonitoringStatusFilter(st) {
  stateV2.monitoring.statusFilter = st;
  document.querySelectorAll("#monStatusFilters .filter-btn-pill").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.status === st);
  });
  renderMonitoringV2();
}

function renderMonitoringV2() {
  const tbody = document.getElementById("monitoringTableBodyV2");
  const countEl = document.getElementById("monFilterCount");
  if (!tbody) return;

  const q = stateV2.monitoring.searchQuery;
  const fSt = stateV2.monitoring.statusFilter;

  const filtered = stateV2.monitoring.sources.filter(s => {
    const matchQ = !q ||
      s.source_id.toLowerCase().includes(q) ||
      (s.domain && s.domain.toLowerCase().includes(q)) ||
      (s.description && s.description.toLowerCase().includes(q)) ||
      (s.adapter && s.adapter.toLowerCase().includes(q)) ||
      (s.endpoint_url && s.endpoint_url.toLowerCase().includes(q));

    let matchSt = true;
    if (fSt === "GOOD") matchSt = s.status === "GOOD" || s.status === "UNCHANGED";
    else if (fSt === "ATTENTION") matchSt = s.status === "ATTENTION";
    else if (fSt === "ERROR") matchSt = s.status === "ERROR";
    else if (fSt === "DUE") matchSt = s.is_due === true;

    return matchQ && matchSt;
  });

  if (countEl) countEl.textContent = `${filtered.length} flux affiché${filtered.length > 1 ? "s" : ""}`;

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align:center;padding:2.5rem;color:var(--text-muted);">
          Aucun flux ne correspond aux filtres sélectionnés.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = filtered.map(s => {
    const pillClass = s.status.toLowerCase();
    const scoreColor = s.trust_score >= 85 ? "var(--gov-green)" : (s.trust_score >= 60 ? "var(--gov-warning)" : "var(--gov-danger)");
    const rowsStatus = s.min_rows_passed
      ? `<span style="color:var(--gov-green);font-size:0.75rem;">✓ Seuil lignes atteint (min ${s.min_rows})</span>`
      : `<span style="color:var(--gov-danger);font-size:0.75rem;">✗ Lignes insuffisantes (${s.row_count} / min ${s.min_rows})</span>`;

    const mutBadge = (s.last_changed_utc && s.last_changed_utc === s.last_checked_utc)
      ? `<span style="color:var(--gov-green);font-size:0.75rem;font-weight:600;">⚡ Nouvelle mutation</span>`
      : `<span style="color:var(--text-muted);font-size:0.75rem;">Empreinte stable (SHA-256)</span>`;

    const dueBadge = s.is_due
      ? `<span class="mon-due-badge due">⏳ Échu (Exécution due)</span>`
      : `<span class="mon-due-badge waiting">Dans ~${Math.max(1, Math.ceil(s.seconds_until_due / 60))} min</span>`;

    const historyDots = (s.history || []).slice(-7).map(h => {
      const col = h.status === "GOOD" || h.status === "UNCHANGED" ? "var(--gov-green)" : (h.status === "ATTENTION" ? "var(--gov-warning)" : "var(--gov-danger)");
      return `<span class="mon-history-dot" style="background:${col};" title="${h.status} (${h.checked_at})"></span>`;
    }).join("");

    return `
      <tr class="mon-row">
        <td>
          <div style="font-weight:700;color:var(--text-primary);font-size:0.95rem;">${s.source_id}</div>
          <div style="margin-top:0.25rem;">
            <span class="dm-domain-tag">${s.domain}</span>
            <span class="mono" style="font-size:0.7rem;color:var(--text-muted);">${s.license_spdx || 'Open'}</span>
          </div>
          <div style="font-size:0.78rem;color:var(--text-secondary);margin-top:0.35rem;line-height:1.4;">${s.description || ''}</div>
          ${s.error_message ? `<div class="mon-err-box">⚠️ <strong>Anomalie :</strong> ${s.error_message}</div>` : ''}
        </td>
        <td>
          <span class="mon-status-pill ${pillClass}">
            <span style="width:6px;height:6px;border-radius:50%;background:currentColor;display:inline-block;"></span>
            ${s.status}
          </span>
          <div style="font-size:0.78rem;color:var(--text-muted);margin-top:0.35rem;">
            Contrôle : <strong>${formatRelativeTime(s.last_checked_utc)}</strong>
          </div>
          ${historyDots ? `<div class="mon-mini-history" title="Historique récent des runs">${historyDots}</div>` : ''}
        </td>
        <td>
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;font-weight:600;">Trust Score</span>
            <span class="mono" style="font-weight:800;color:${scoreColor};font-size:0.95rem;">${s.trust_score.toFixed(1)}%</span>
          </div>
          <div class="mon-quality-bar">
            <div class="mon-quality-bar-fill" style="width:${Math.min(100, Math.max(5, s.trust_score))}%;background:${scoreColor};"></div>
          </div>
          <div style="margin-top:0.4rem;">
            ${rowsStatus}
          </div>
          <div style="font-size:0.72rem;color:var(--text-muted);margin-top:0.15rem;">
            ✓ ${(s.required_fields || []).length} champs requis certifiés
          </div>
        </td>
        <td>
          <div style="display:flex;align-items:center;gap:0.4rem;flex-wrap:wrap;">
            <span class="mon-source-badge ${s.source_used}">${s.source_used}</span>
            <code class="mono" style="font-size:0.72rem;padding:0.15rem 0.35rem;background:var(--bg-code);border-radius:3px;">${s.adapter}</code>
          </div>
          <a href="${s.endpoint_url}" target="_blank" rel="noopener" class="mono" style="font-size:0.72rem;color:var(--text-muted);margin-top:0.4rem;display:inline-block;word-break:break-all;max-width:240px;text-decoration:none;" title="${s.endpoint_url}">
            🔗 ${s.endpoint_url}
          </a>
        </td>
        <td>
          <div class="mono" style="font-size:1.05rem;font-weight:800;color:var(--text-primary);">${s.row_count.toLocaleString()} <span style="font-size:0.75rem;font-weight:500;color:var(--text-muted);">lignes</span></div>
          <div style="margin-top:0.25rem;">
            ${mutBadge}
          </div>
          <div class="mono" style="font-size:0.68rem;color:var(--text-muted);margin-top:0.25rem;" title="${s.sha256}">
            SHA: ${s.sha256 ? s.sha256.substring(0, 10) + '...' : '-'}
          </div>
        </td>
        <td>
          <div style="font-size:0.8rem;color:var(--text-secondary);">
            Cadence : <strong>${s.cadence_minutes} min</strong> (SLA ${s.sla_minutes}m)
          </div>
          <div style="margin-top:0.25rem;">
            ${dueBadge}
          </div>
          <div style="font-size:0.72rem;color:var(--text-muted);margin-top:0.35rem;">
            Mutation : ${formatRelativeTime(s.last_changed_utc)}
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

// Rendu du Catalogue
function healthOfV2(d) {
  const ids = (d.sources || []).map(s => s.source_id);
  const st = stateV2.monitoring.sources.filter(s => ids.includes(s.source_id)).map(s => s.status);
  if (!st.length) return null;
  if (st.includes("ERROR")) return ["ERROR", "var(--gov-danger)"];
  if (st.includes("ATTENTION")) return ["ATTENTION", "var(--gov-warning)"];
  return ["GOOD", "var(--gov-green)"];
}

function coverageV2(d) {
  return d.coverage ? `${String(d.coverage.from).slice(0, 10)} → ${String(d.coverage.to).slice(0, 10)}` : "—";
}

function renderCatalogV2() {
  const container = document.getElementById("datamartsGridV2");
  const countEl = document.getElementById("catalogCountV2");
  if (!container) return;
  const q = stateV2.searchQuery.toLowerCase();
  const filtered = stateV2.datasets.filter(d => {
    const matchDomain = stateV2.selectedDomain === "all" || d.domain === stateV2.selectedDomain;
    const hay = `${d.dataset} ${d.title} ${sourceLabelV2(d)}`.toLowerCase();
    return matchDomain && (!q || hay.includes(q));
  });
  if (countEl) countEl.textContent = `${filtered.length} table${filtered.length > 1 ? "s" : ""} Gold`;
  if (!filtered.length) {
    container.innerHTML = `<p style="color:var(--text-muted);">Aucune table disponible : lancez <code>uv run openlux run</code>.</p>`;
    return;
  }
  container.innerHTML = filtered.map(d => {
    const h = healthOfV2(d);
    const origins = [...new Set((d.sources || []).map(s => s.data_origin))].join(" / ");
    const lic = [...new Set((d.sources || []).map(s => s.license_spdx))].join(", ");
    return `
    <div class="datamart-card-v2" onclick="openDrawerV2('${escapeHtmlV2(d.dataset)}')">
      <div>
        <div class="dm-card-top">
          <span class="dm-domain-tag">${escapeHtmlV2(d.domain)}</span>
          ${h ? `<span class="mono" style="font-size:0.7rem;font-weight:700;color:${h[1]};">${h[0]}</span>` : ""}
        </div>
        <h3 class="dm-title">${escapeHtmlV2(d.title)}</h3>
        <div class="dm-source-origin"><span class="mono">${escapeHtmlV2(d.dataset)}</span></div>
        <p class="dm-desc">Sources : ${escapeHtmlV2(sourceLabelV2(d))}<br>Nature : ${escapeHtmlV2(origins || "—")}<br>Couverture : ${escapeHtmlV2(coverageV2(d))}</p>
      </div>
      <div class="dm-bottom-meta">
        <span class="mono" style="color:var(--text-primary);font-weight:600;">${(d.row_count || 0).toLocaleString("fr-FR")} lignes</span>
        <span class="mono" style="color:var(--lux-blue);font-weight:600;">${escapeHtmlV2(lic)}</span>
      </div>
    </div>`;
  }).join("");
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
  const setText = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
  const first = (d.sources || [])[0] || {};
  setText("drawerTitleV2", d.title);
  setText("drawerDomainV2", d.domain);
  setText("drawerDescV2", (d.sources || []).map(s => s.description).join(" • "));
  setText("drawerSourceOrgV2", sourceLabelV2(d));
  const linkEl = document.getElementById("drawerSourceUrlV2");
  linkEl.href = first.url || "#";
  linkEl.textContent = first.url || "—";
  setText("drawerCadenceV2", coverageV2(d));
  setText("drawerSlaV2", d.time_column ? `colonne ${d.time_column}` : "");
  setText("drawerLastRefreshV2", d.last_collected_utc || "—");
  const h = healthOfV2(d);
  setText("drawerStatusV2", h ? `Statut des sources : ${h[0]}` : "Statut : API de supervision non joignable");
  const ids = (d.sources || []).map(s => s.source_id);
  const scores = stateV2.monitoring.sources.filter(s => ids.includes(s.source_id)).map(s => s.trust_score);
  setText("drawerTrustV2", scores.length ? `${Math.min(...scores).toFixed(1)} (min)` : "–");
  setText("drawerRowsV2", (d.row_count || 0).toLocaleString("fr-FR"));
  setText("drawerLicenseV2", [...new Set((d.sources || []).map(s => s.license_spdx))].join(", "));
  const srcBox = document.getElementById("drawerSourcesV2");
  if (srcBox) {
    srcBox.innerHTML = (d.sources || []).map(s => `
      <div style="margin-bottom:0.5rem;">
        <strong class="mono">${escapeHtmlV2(s.source_id)}</strong> — ${escapeHtmlV2(s.license_spdx)} — ${escapeHtmlV2(s.data_origin)}${s.commercial_use_safe ? "" : " — usage commercial non garanti"}<br>
        <a href="${escapeHtmlV2(s.url)}" target="_blank" rel="noopener" class="mono" style="word-break:break-all;">${escapeHtmlV2(s.url)}</a><br>
        <span style="color:var(--text-muted);">Limites : ${escapeHtmlV2(s.known_limitations)}</span>
      </div>`).join("");
  }
  const tbody = document.getElementById("drawerSchemaBodyV2");
  tbody.innerHTML = (d.columns || []).map(c => `
    <tr>
      <td class="mono font-heading" style="color:var(--text-primary)">${escapeHtmlV2(c.name)}</td>
      <td class="mono" style="color:var(--lux-blue)">${escapeHtmlV2(c.type)}</td>
      <td>${c.name === d.time_column ? "Colonne temporelle" : ""}</td>
    </tr>`).join("");
  setText("drawerSqlCodeV2", `SELECT * FROM read_parquet('data/gold/${d.dataset}.parquet') LIMIT 50;`);
  setText("drawerMcpCodeV2", `call_mcp_tool(server='openlux', tool='query_dataset', arguments={'dataset': '${d.dataset}', 'limit': 20})`);
  document.getElementById("btnDlParquetV2").href = `/v1/exports/${d.dataset}.parquet`;
  document.getElementById("btnDlCsvV2").href = `/v1/exports/${d.dataset}.csv`;
  document.getElementById("drawerBackdropV2").classList.add("open");
  document.getElementById("drawerPanelV2").classList.add("open");
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
