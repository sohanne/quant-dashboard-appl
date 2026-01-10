# Quant Dashboard — AAPL (Quant A) + Portfolio (Quant B)

Mini pipeline “quant” déployée sur une VM AWS (Ubuntu) :
- collecte automatique de prix
- stockage CSV
- dashboard Streamlit (stratégies + métriques)
- module portfolio multi-actifs (Quant B)
- report quotidien automatisé

---

## Liens
- Repo : https://github.com/sohanne/quant-dashboard-appl
- Dashboard (EC2) : http://35.180.98.225:8501  
  ➜ Le module **Portfolio (Quant B)** est accessible via **la sidebar Streamlit** (page “Portfolio”).

---

## Données & sources
### Quant A — AAPL intraday
- Actif : AAPL
- Bootstrap historique : Yahoo Finance via `yfinance`  
  Commande : `python -u src/app.py history`
- Collecte live : Finnhub API toutes les 5 minutes (cron)  
  Commande : `python src/app.py once`
- Fichier de données : `data/aapl_prices.csv` (colonnes : `timestamp_utc`, `price`)

### Quant B — Portfolio multi-actifs
- Données marché : Yahoo Finance via `yfinance`
- Les prix sont téléchargés à la demande dans le dashboard (pas stockés dans `data/aapl_prices.csv`).

---

## Structure du repo
- `src/app.py` : collecte AAPL (once/loop) + bootstrap historique (history)
- `src/dashboard.py` : page Streamlit principale (Quant A)
- `src/pages/1_Portfolio.py` : page Streamlit secondaire (Quant B) (multipage)
- `src/ui/portfolio_page.py` : UI Portfolio Quant B
- `src/portfolio/` : backtest + métriques + plots (Quant B)
- `scripts/` : scripts Linux (report quotidien)
- `data/` : CSV AAPL (local/VM)
- `reports/` : logs + reports (`fetch.log`, `streamlit.log`, reports…)

---

## Requirements
Voir `requirements.txt` :
- streamlit
- streamlit-autorefresh
- pandas, numpy
- requests
- python-dotenv
- yfinance
- plotly

---

## API key (ne pas commiter)
Le mode live (Quant A) utilise Finnhub :
- définir `FINNHUB_API_KEY` via `.env` ou variable d’environnement sur la VM.

Exemple `.env` (sur la VM) :
FINNHUB_API_KEY=xxxx

---

## Usage (local)
```bash
# venv + deps
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# bootstrap historique AAPL
python -u src/app.py history

# une mesure Finnhub
python src/app.py once

# dashboard
streamlit run src/dashboard.py

---
