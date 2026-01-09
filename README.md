# AAPL Dashboard (Projet Git / Linux / Python)

## Quant A

## Quant A

## Objectif
Mettre en place une mini “pipeline quant” autour d’AAPL :
- collecte de prix intraday automatiquement (cron)
- stockage dans un CSV
- dashboard Streamlit interactif (stratégies + métriques)
- report quotidien automatisé

## Liens
- Repo : https://github.com/sohanne/quant-dashboard-appl
- Dashboard : http://ec2-35-180-98-225.eu-west-3.compute.amazonaws.com:8501/
- SSH VM :
  ```powershell
  ssh -i C:\Users\sohan\.ssh\aws.pem ubuntu@ec2-35-180-98-225.eu-west-3.compute.amazonaws.com

## Données
- Actif principal : AAPL (Apple)
- Bootstrap historique (one-shot) : Yahoo Finance via yfinance (python src/app.py history)
- Collecte live (toutes les 5 minutes) : Finnhub API (python src/app.py once via cron)
- Fichier de données : data/aapl_prices.csv (colonnes : timestamp_utc, price)

## Structure du repo
- src/app.py : collecte (once/loop) + bootstrap historique (history)
- src/dashboard.py : dashboard Streamlit (périodicité, stratégies, métriques)
- scripts/ : scripts Linux (report quotidien)
- data/ : CSV de prix (local/VM)
- reports/ : logs + reports (fetch.log, streamlit.log, report quotidien…)

## API Key (ne pas commiter)
Le mode live utilise Finnhub :

- à définir sur la machine d’exécution via .env ou variable d’environnement :
    - FINNHUB_API_KEY=...

## Usage (local)
- 1 mesure : `python src/app.py once`
- refresh 5 min : `python src/app.py loop`
- Bootstrap historique :`python src/app.py history`

### Déploiement sur VM AWS(Ubuntu)
- Connexion SSH: `ssh -i ~/.ssh/aws.pem ubuntu@ec2-35-180-98-225.eu-west-3.compute.amazonaws.com`
- Récupération du projet: 
`cd /home/ubuntu/quant-dashboard-appl`
`git pull`
- Activer la venv + installer les dépendances: 
`source .venv/bin/activate`
`pip install -r requirements.txt`
- Bootstrap historique :
`python -u src/app.py history`
`wc -l data/aapl_prices.csv`
- Lancer Streamlit:
`pkill -f streamlit || true`
`nohup /home/ubuntu/quant-dashboard-appl/.venv/bin/streamlit run /home/ubuntu/quant-dashboard-appl/src/dashboard.py \`
  `--server.address 0.0.0.0 --server.port 8501 \`
  `> /home/ubuntu/quant-dashboard-appl/reports/streamlit.log 2>&1 &`

### Cron (collecte automatique + report)
Collecte toutes les 5 minutes + report quotidien: `crontab -l`
Exemples utilisés :
- */5 * * * * : collecte AAPL toutes les 5 minutes → `reports/fetch.log`
- 0 20 * * * : report quotidien → `reports/cron.log`

### Dashboard (Stratégie +métriques)
Le dashboard permet: 
- choix périodicité : Raw / 15min / 1H / 1D
- choix stratégie : Buy & Hold / Momentum (window)
- métriques : total return, max drawdown, volatilité annualisée (approx), Sharpe (approx)
- auto-refresh toutes les 5 minutes

Astuce : pour voir un signal plus vite :
- stratégie = Momentum
- window = 3 ou 5
- périodicité = Raw

### Debug/correction (incident cron)
- Symptôme :
`reports/fetch.log` indiquait des écritures `[OK]` mais le fichier `data/aapl_prices.csv` du projet ne se remplissait pas.

- Cause :
cron exécute le script avec un répertoire courant différent → les chemins relatifs écrivaient dans `/home/ubuntu/` au lieu du repo.

- Fix :
calcul d’un `BASE_DIR` à partir de `__file__` et écriture en chemin absolu dans :
`/home/ubuntu/quant-dashboard-appl/data/aapl_prices.csv`

- Preuve :
à partir de `2026-01-09T14:05:02+00:00`, le log indique l’écriture dans
`/home/ubuntu/quant-dashboard-appl/data/aapl_prices.csv`


## Quant B — Portfolio Module

The Quant B module implements a multi-asset portfolio analysis and backtesting tool.
It allows users to build, analyze and monitor diversified portfolios using historical market data.

### Features
- Selection of at least three financial assets
- Equal-weight or custom-weight portfolio allocation
- Portfolio backtesting with periodic rebalancing (weekly, monthly, quarterly)
- Performance metrics:
  - Annualized return
  - Annualized volatility
  - Sharpe ratio
  - Maximum drawdown
  - Diversification effect
- Asset correlation matrix
- Interactive visualizations (prices, cumulative performance)
- Automated daily portfolio reports exported as CSV files

### Daily Portfolio Report
A daily portfolio report can be generated from the command line:

bash
python -m src.portfolio.daily_report 


The report is saved in the reports/ directory and includes key portfolio performance metrics.

### Data Source
Market data is retrieved using Yahoo Finance via the yfinance Python library.

### Academic Context
This module was developed independently as part of the Quant B assignment and later integrated into a single Streamlit dashboard with the Quant A module, as required by the course.

