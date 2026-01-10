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

## API key 
Le mode live (Quant A) utilise Finnhub :
- définir `FINNHUB_API_KEY` via `.env` ou variable d’environnement sur la VM.

Exemple `.env` (sur la VM) :
FINNHUB_API_KEY=xxxx

---

## Usage
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

```

---


##Déploiement sur VM AWS (Ubuntu)

###1) Connexion SSH
```bash
ssh -i ~/.ssh/aws.pem ubuntu@ec2-35-180-98-225.eu-west-3.compute.amazonaws.com
```

###2) Pull + deps + restart (à faire après chaque merge)
cd /home/ubuntu/quant-dashboard-appl
```bash
git switch main
git pull

source .venv/bin/activate
pip install -r requirements.txt

sudo systemctl restart streamlit-quant
sudo systemctl status streamlit-quant --no-pager
```

---


###3) Bootstrap historique
```bash
source .venv/bin/activate
python -u src/app.py history
wc -l data/aapl_prices.csv
```

---


## Cron (collecte + report)

Exemple crontab -l sur la VM :

- collecte AAPL toutes les 5 minutes → log dans reports/fetch.log
- report quotidien → log dans reports/cron.log


---


## Accès public

Pour que le site soit accessible à tout le monde :

- AWS EC2 Security Group → Inbound rules :

    - TCP 8501 ouvert à 0.0.0.0/0


---


## Quant A — Dashboard (stratégies & métriques)

Fonctionnalités :

- périodicité : Raw / 15min / 1H / 1D
- Buy & Hold vs Momentum (window + frais de trading)
- métriques : total return, max drawdown, volatilité annualisée (approx), Sharpe (approx), win rate
- auto-refresh toutes les 5 minutes


---


## Quant B — Portfolio Module

Fonctionnalités :

- sélection >= 3 actifs (actions, ETF, crypto)
- allocation equal-weight ou custom
- rebalancing : Never / Weekly / Monthly / Quarterly
- métriques : annualized return, vol, Sharpe, max drawdown, diversification effect
- heatmap de corrélation + charts Plotly

Lancer le report portfolio en CLI
```bash
python -m src.portfolio.daily_report
```
Le report est sauvegardé dans reports/ (CSV).

---



## Debug — incident cron (chemins relatifs)

Problème rencontré :
- reports/fetch.log affichait [OK] mais data/aapl_prices.csv ne se remplissait pas.

Cause :
- cron exécute avec un répertoire courant différent → chemins relatifs écrivaient ailleurs.

Fix :
- calcul d’un BASE_DIR à partir de __file__ et écriture en chemin absolu dans :
/home/ubuntu/quant-dashboard-appl/data/aapl_prices.csv
