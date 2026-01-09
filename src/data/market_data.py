import pandas as pd
import yfinance as yf


def get_prices(tickers: list[str], period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    """
Download historical price data for a list of assets using Yahoo Finance.
The function returns adjusted prices for the selected tickers over the chosen time period and frequency.
Parameters
tickers : list[str]
    List of asset tickers to download.
period : str
    Time window used to retrieve the data (e.g. "1y", "2y").
interval : str
    Data frequency (e.g. daily "1d", weekly "1wk").

Returns
pd.DataFrame
    DataFrame indexed by date with one column per ticker.
    Returns an empty DataFrame if the download fails.
"""

    # Defensive: allow a single ticker passed as string
    if isinstance(tickers, str):
        tickers = [tickers]

    if not tickers:
        return pd.DataFrame()

    try:
        data = yf.download(
            tickers=tickers,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
        )

        # yfinance returns MultiIndex columns when multiple tickers
        if isinstance(data.columns, pd.MultiIndex):
            # "Close" exists even with auto_adjust=True
            prices = data["Close"].copy()
        else:
            # Single ticker: columns not MultiIndex -> build a consistent DF
            prices = data[["Close"]].rename(columns={"Close": tickers[0]}).copy()

        # Clean index / rows
        prices.index = pd.to_datetime(prices.index, errors="coerce")
        prices = prices.dropna().sort_index()

        return prices

    except Exception:
        return pd.DataFrame()
    

