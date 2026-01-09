# AAPL Dashboard (Projet Git/Linux/Python)

## Objectif
Dashboard interactif qui récupère des données en continu, affiche la valeur actuelle, trace un graphique time series et génère un report quotidien automatisé.

## Données
- Actif principal : AAPL (Apple)
- Source : Finnhub (API)

## Structure du repo
- `src/` : code de l'application (dashboard)
- `scripts/` : scripts Linux (cron, report quotidien)
- `data/` : données locales (historique)
- `reports/` : reports journaliers

## API Key (ne pas commiter)
- Définir `FINNHUB_API_KEY` sur la machine d’exécution

## Cron (report quotidien)
- Script : `scripts/daily_report.sh`
- Cron : à compléter (ex : 20:00)

## Usage (local)
- 1 mesure : `python src/app.py once`
- refresh 5 min : `python src/app.py loop`

## Report quotidien
Le script `scripts/daily_report.sh` génère un report texte dans `reports/`.

### Exécution manuelle (sur Linux/VM)
```bash
chmod +x scripts/daily_report.sh
./scripts/daily_report.sh

## Run (VM AWS)

### 1) SSH
ssh -i ~/.ssh/aws.pem ubuntu@<EC2_HOST>

### 2) Update repo
cd /home/ubuntu/quant-dashboard-appl
git pull

### 3) Activate venv + install deps
source .venv/bin/activate
pip install -r requirements.txt

### 4) Bootstrap history (remplit data/aapl_prices.csv)
python -u src/app.py history

### 5) Run Streamlit
pkill -f streamlit || true
nohup /home/ubuntu/quant-dashboard-appl/.venv/bin/streamlit run /home/ubuntu/quant-dashboard-appl/src/dashboard.py \
  --server.address 0.0.0.0 --server.port 8501 \
  > /home/ubuntu/quant-dashboard-appl/reports/streamlit.log 2>&1 &

