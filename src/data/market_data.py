import yfinance as yf
import pandas as pd

def get_prices(tickers, period="2y", interval="1d"):
    """
    Download historical close prices for a list of tickers.
    Returns a DataFrame indexed by date.
    """
    try:
        data = yf.download(
            tickers,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False
        )

        if isinstance(data.columns, pd.MultiIndex):
            prices = data["Close"]
        else:
            prices = data.to_frame(name=tickers[0])

        return prices.dropna()

    except Exception:
        return pd.DataFrame()
    

