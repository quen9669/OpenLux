# Guide de Déploiement du Monitoring sur VPS & Grafana

Ce guide explique comment brancher le monitoring d'OpenLux Hub sur une instance Grafana hébergée sur votre VPS, une fois les métriques validées en local.

---

## 1. Deux Méthodes d'Intégration au Choix

### Option A : Via le standard Prometheus (Recommandé)
Le backend FastAPI d'OpenLux Hub expose nativement un endpoint `/metrics` au format texte standard Prometheus, **sans aucune dépendance lourde**.

1. **Sur votre VPS (Prometheus / Grafana Agent / Alloy)** :
   Ajoutez un job de scrape dans votre `prometheus.yml` :
   ```yaml
   scrape_configs:
     - job_name: 'openlux_hub'
       scrape_interval: 30s
       metrics_path: '/metrics'
       static_configs:
         - targets: ['127.0.0.1:8000'] # ou l'IP interne/hôte de votre conteneur
   ```

2. **Dans Grafana** :
   - Allez dans **Dashboards** $\rightarrow$ **New** $\rightarrow$ **Import**.
   - Uploadez ou collez le contenu du fichier [`dashboard_openlux_hub.json`](file:///docs/grafana/dashboard_openlux_hub.json).
   - Sélectionnez votre source de données Prometheus (`DS_PROMETHEUS`).
   - Le dashboard s'affiche immédiatement avec :
     - La frise d'état temporelle (*State Timeline*) de chaque flux (vert, jaune, rouge).
     - Les jauges de Trust Score et les volumes de lignes collectées.
     - Les alertes de dégradation ou d'erreur.

---

### Option B : Via le Plugin Grafana Infinity (Direct Zéro-Prometheus)
Si vous ne souhaitez pas installer Prometheus sur votre VPS et préférez que Grafana interroge directement l'API FastAPI :

1. Installez le plugin officiel Grafana [**Infinity**](https://grafana.com/grafana/plugins/yesoreyeram-infinity-datasource/) :
   ```bash
   grafana-cli plugins install yesoreyeram-infinity-datasource
   ```
2. Créez une nouvelle source de données **Infinity** pointant vers l'URL de votre API OpenLux Hub :
   - URL : `http://127.0.0.1:8000`
3. Créez des panneaux en sélectionnant la source Infinity :
   - Type : `JSON`
   - URL : `/v1/status`
   - Root selector : `sources`
   - Vous avez accès à tous les champs en direct : `source_id`, `status`, `trust_score`, `row_count`, `min_rows_passed`, `adapter`, `last_checked_utc`, `next_run_due_utc`, `error_message`.

---

## 2. Métriques Exposées par OpenLux Hub

| Nom de la Métrique | Type | Labels | Description |
| :--- | :---: | :--- | :--- |
| `openlux_flow_status` | Gauge | `source_id`, `domain` | Statut d'exécution (`1.0` = GOOD/UNCHANGED, `0.5` = ATTENTION, `0.0` = ERROR) |
| `openlux_flow_trust_score` | Gauge | `source_id`, `domain` | Score de confiance composite (0.0 à 100.0) |
| `openlux_flow_rows_collected` | Gauge | `source_id`, `domain` | Quantité exacte de lignes/entités extraites |
| `openlux_flow_last_run_timestamp_seconds` | Gauge | `source_id`, `domain` | Horodatage Unix du dernier run d'ingestion |

---

## 3. Alerting Automatique

OpenLux Hub intègre nativement un webhook anti-spam (`OPENLUX_ALERT_WEBHOOK_URL`) qui alerte vers Discord ou Telegram dès qu'un flux passe à `ERROR` ou après 3 alertes consécutives `ATTENTION`.
Sur Grafana, vous pouvez également configurer des règles d'alerting Grafana Managed Alerts basées sur l'expression `openlux_flow_status == 0`.
