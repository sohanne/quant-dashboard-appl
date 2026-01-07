import os
import csv
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv


def get_aapl_price_finnhub(api_key):
    """
    Récupère le prix actuel de AAPL via Finnhub (endpoint 'quote').
    """
    url = "https://finnhub.io/api/v1/quote"
    params = {"symbol": "AAPL", "token": api_key}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    price = data.get("c")  # current price
    if price is None:
        raise ValueError(f"Réponse Finnhub inattendue: {data}")
    return float(price)


def append_to_csv(csv_path, timestamp_iso, price):
    """
    Ajoute une ligne (timestamp, price) dans un CSV.
    """
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp_utc", "price"])
        writer.writerow([timestamp_iso, price])


def main():
    # Charge .env (FINNHUB_API_KEY=...)
    load_dotenv()
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        raise RuntimeError(
            "FINNHUB_API_KEY introuvable. Crée un fichier .env à la racine avec:\n"
            "FINNHUB_API_KEY=TA_CLE_ICI"
        )

    price = get_aapl_price_finnhub(api_key)

    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

    os.makedirs("data", exist_ok=True)
    csv_path = os.path.join("data", "aapl_prices.csv")
    append_to_csv(csv_path, ts, price)

    print(f"[OK] {ts} AAPL={price} (écrit dans {csv_path})")


if __name__ == "__main__":
    import time
    import sys
    from datetime import datetime

    # Utilisation :
    #   python src/app.py once
    #   python src/app.py loop
    mode = "once"
    if len(sys.argv) >= 2:
        mode = sys.argv[1].lower()

    if mode == "loop":
        while True:
            try:
                main()
            except Exception as e:
                print(f"[ERROR] {e}")
            print(f"[INFO] next run in 5 minutes ({datetime.now().isoformat(timespec='seconds')})")
            time.sleep(300)  # 5 minutes
    else:
        main()
