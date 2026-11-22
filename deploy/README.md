# Déploiement en Production sur VPS — OpenLux Hub

Ce guide explique comment faire tourner OpenLux Hub en continu 24/7 sur votre VPS pour ne perdre aucune donnée et alimenter votre Grafana.

---

## 1. Pourquoi le VPS est supérieur à GitHub Actions sur le long terme

| Critère | GitHub Actions | VPS Linux (Recommandé) |
| :--- | :--- | :--- |
| **Cadence (15 min)** | 2 880 runs/mois $\rightarrow$ dépasse le quota gratuit (2 000 min) | **Illimité, 0 € de surcoût** (consomme < 2 % CPU) |
| **Persistance des données** | Éphémère (obligation d'envoyer les parquets sur S3 ou de polluer git) | **Disque SSD local natif** (`data/bronze/`, DuckDB, `data/gold/`) |
| **Ponctualité (Jitter)** | Décalage fréquent de 15 à 60 min aux heures de pointe | **Ponctuel à la seconde près** |
| **Métriques Prometheus** | Complexe (nécessite Pushgateway) | **Scraping direct local** : Prometheus scrape `http://127.0.0.1:8000/metrics` |

---

## 2. Déploiement en 3 étapes sur le VPS

### Étape 1 : Cloner le dépôt et installer `uv`
```bash
sudo useradd -m -s /bin/bash openlux
sudo git clone https://github.com/quen9669/OpenLux.git /opt/openlux-hub
sudo chown -R openlux:openlux /opt/openlux-hub

# Installer uv pour l'utilisateur openlux
sudo -u openlux curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Étape 2 : Lancer le premier run d'initialisation
```bash
cd /opt/openlux-hub
sudo -u openlux /home/openlux/.cargo/bin/uv sync
sudo -u openlux /home/openlux/.cargo/bin/uv run openlux run
```

### Étape 3 : Activer les services systemd

Copiez les deux fichiers de service dans `/etc/systemd/system/` :
```bash
sudo cp /opt/openlux-hub/deploy/openlux.service /etc/systemd/system/
sudo cp /opt/openlux-hub/deploy/openlux-scheduler.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now openlux
sudo systemctl enable --now openlux-scheduler
```

Vérifiez l'état des services :
```bash
sudo systemctl status openlux
sudo systemctl status openlux-scheduler
```

L'API est accessible sur `http://VOTRE_IP_VPS:8000/` et le dashboard sur `http://VOTRE_IP_VPS:8000/v2/`.

---

## 3. Raccordement à Prometheus & Grafana sur le VPS

Ajoutez le job de scraping dans votre `/etc/prometheus/prometheus.yml` :
```yaml
scrape_configs:
  - job_name: 'openlux_hub'
    scrape_interval: 30s
    static_configs:
      - targets: ['localhost:8000']
        labels:
          env: 'production'
          region: 'luxembourg'
```

Puis importez le dashboard Grafana fourni dans [docs/grafana/dashboard_openlux_hub.json](../docs/grafana/dashboard_openlux_hub.json).
