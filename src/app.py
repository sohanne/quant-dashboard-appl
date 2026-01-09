import os
import csv
import time
import sys
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv


def get_aapl_price_finnhub(api_key: str) -> float:
    url = "https://finnhub.io/api/v1/quote"
    params = {"symbol": "AAPL", "token": api_key}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    price = data.get("c")  # current price
    if price is None:
        raise ValueError(f"Réponse Finnhub inattendue: {data}")
    return float(price)


def bootstrap_history_yahoo(symbol: str = "AAPL"):
    """
    Bootstraps intraday history from Yahoo Finance via yfinance.
    Tries to get a lot of points:
      - 1m over 7d (max intraday depth)
      - fallback: 5m over 30d
    Returns list of (timestamp_iso_utc, close_price).
    """
    import yfinance as yf

    tries = [
        {"interval": "1m", "period": "7d"},
        {"interval": "5m", "period": "30d"},
    ]

    last_err = None
    for t in tries:
        try:
            df = yf.download(
                tickers=symbol,
                period=t["period"],
                interval=t["interval"],
                progress=False,
                auto_adjust=False,
                prepost=True,
                threads=False,
            )
            if df is None or df.empty:
                raise RuntimeError(f"Yahoo returned empty df for {t}")

            # handle Close column (usually "Close")
            if "Close" not in df.columns:
                raise RuntimeError(f"Close column not found. columns={df.columns}")

            s = df["Close"].dropna()
            if s.empty:
                raise RuntimeError("Close series empty after dropna().")

            idx = s.index
            if getattr(idx, "tz", None) is None:
                idx = idx.tz_localize("UTC")
            else:
                idx = idx.tz_convert("UTC")

            rows = []
            for dt, close in zip(idx, s.values):
                dt_iso = dt.to_pydatetime().replace(tzinfo=timezone.utc).isoformat(timespec="seconds")
                rows.append((dt_iso, float(close)))

            if len(rows) < 100:
                raise RuntimeError(f"Too few points ({len(rows)}) for {t}, trying fallback...")

            return rows

        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(f"Yahoo history failed after fallbacks: {last_err}")



def append_to_csv(csv_path: str, timestamp_iso: str, price: float):
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp_utc", "price"])
        writer.writerow([timestamp_iso, price])


def main():
    # chemins absolus (repo)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, "aapl_prices.csv")

    # mode CLI
    mode = sys.argv[1].lower() if len(sys.argv) >= 2 else "once"

    # Charge .env (chemin explicite)
    env_path = os.path.join(BASE_DIR, ".env")
    load_dotenv(dotenv_path=env_path)

    # MODE HISTORY : Yahoo (pas besoin de FINNHUB_API_KEY) ----
    if mode == "history":
        rows = bootstrap_history_yahoo("AAPL")  # <= c'est ça le changement clé
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp_utc", "price"])
            for dt, p in rows:
                writer.writerow([dt, p])
        print(f"[OK] Yahoo history written: {len(rows)} points -> {csv_path}")
        return

    # MODE ONCE / LOOP : Finnhub (clé obligatoire ici) ----
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        raise RuntimeError(
            "FINNHUB_API_KEY introuvable. Crée un fichier .env à la racine avec:\n"
            "FINNHUB_API_KEY=TA_CLE_ICI"
        )

    price = get_aapl_price_finnhub(api_key)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    append_to_csv(csv_path, ts, price)
    print(f"[OK] {ts} AAPL={price} (écrit dans {csv_path})")

    

if __name__ == "__main__":
    mode = sys.argv[1].lower() if len(sys.argv) >= 2 else "once"

    if mode == "loop":
        while True:
            try:
                main()
            except Exception as e:
                print(f"[ERROR] {e}")
            print(f"[INFO] next run in 5 minutes ({datetime.now().isoformat(timespec='seconds')})")
            time.sleep(300)
    else:
        main()