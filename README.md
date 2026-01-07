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
