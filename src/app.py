import os
import csv
from datetime import datetime, timezone
import time
import sys

import requests
from dotenv import load_dotenv


def get_aapl_price_finnhub(api_key):
    url = "https://finnhub.io/api/v1/quote"
    params = {"symbol": "AAPL", "token": api_key}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    price = data.get("c")  # current price
    if price is None:
        raise ValueError(f"Réponse Finnhub inattendue: {data}")
    return float(price)

def bootstrap_history_finnhub(api_key, symbol="AAPL", resolution="5", days=5):
    """
    Télécharge un historique intraday via Finnhub (endpoint /stock/candle)
    et renvoie une liste de tuples (timestamp_iso_utc, close_price).
    resolution: "1", "5", "15", "30", "60", "D" (selon plan Finnhub)
    days: nb de jours dans le passé
    """
    end_ts = int(datetime.now(timezone.utc).timestamp())
    start_ts = end_ts - days * 24 * 3600

    url = "https://finnhub.io/api/v1/stock/candle"
    params = {
        "symbol": symbol,
        "resolution": resolution,
        "from": start_ts,
        "to": end_ts,
        "token": api_key,
    }

    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    j = r.json()

    if j.get("s") != "ok":
        raise ValueError(f"Réponse Finnhub candle inattendue: {j}")

    t = j.get("t", [])
    c = j.get("c", [])
    rows = []
    for ts, close in zip(t, c):
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec="seconds")
        rows.append((dt, float(close)))

    if not rows:
        raise ValueError("Finnhub candle: aucune donnée retournée.")
    return rows


def bootstrap_history_yahoo(symbol="AAPL", interval="5m", period="5d"):
    """
    Télécharge un historique intraday via Yahoo (yfinance) et renvoie
    une liste de tuples (timestamp_iso_utc, close_price).
    """
    import yfinance as yf

    df = yf.download(symbol, interval=interval, period=period, progress=False)
    if df is None or df.empty:
        raise RuntimeError("Yahoo history vide (yfinance). Réessaie plus tard.")

    close = df["Close"].dropna()

    # Convertit l'index en UTC proprement
    idx = close.index
    try:
        # si tz-naive
        if getattr(idx, "tz", None) is None:
            idx = idx.tz_localize("UTC")
        else:
            idx = idx.tz_convert("UTC")
    except Exception:
        # fallback (rare) : force UTC via pandas
        import pandas as pd
        idx = pd.to_datetime(idx, utc=True)

    rows = []
    for ts, p in zip(idx, close.values):
        ts_iso = ts.to_pydatetime().astimezone(timezone.utc).isoformat(timespec="seconds")
        rows.append((ts_iso, float(p)))

    if not rows:
        raise RuntimeError("Yahoo history: aucune ligne construite.")
    return rows

#Ajoute une ligne (timestamp, price) dans un CSV.
def append_to_csv(csv_path, timestamp_iso, price):
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp_utc", "price"])
        writer.writerow([timestamp_iso, price])


def main():
    # chemins absolus (repo) = robuste en cron
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, "aapl_prices.csv")

    # Charge .env DU REPO (si présent)
    dotenv_path = os.path.join(BASE_DIR, ".env")
    load_dotenv(dotenv_path=dotenv_path)

    mode = sys.argv[1].lower() if len(sys.argv) >= 2 else "once"

    # 1) MODE HISTORY : Yahoo intraday (recommandé)
    if mode == "history":
        rows = bootstrap_history_yahoo(symbol="AAPL", interval="5m", period="5d")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp_utc", "price"])
            for dt, p in rows:
                writer.writerow([dt, p])
        print(f"[OK] Yahoo history written: {len(rows)} points -> {csv_path}")
        return

    # 2) MODE ONCE / LOOP : Finnhub quote (dernier prix)
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        raise RuntimeError(
            "FINNHUB_API_KEY introuvable.\n"
            "Sur la VM, crée /home/ubuntu/quant-dashboard-appl/.env avec:\n"
            "FINNHUB_API_KEY=TA_CLE_ICI"
        )

    price = get_aapl_price_finnhub(api_key)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    append_to_csv(csv_path, ts, price)
    print(f"[OK] {ts} AAPL={price} (écrit dans {csv_path})")
