from __future__ import annotations

import os
from datetime import datetime

import pandas as pd

from src.data.market_data import get_prices
from src.portfolio.backtest import backtest_portfolio
from src.portfolio.metrics import (
    annualized_return,
    annualized_vol,
    max_drawdown,
    portfolio_daily_returns,
    sharpe_ratio,
)

DEFAULT_TICKERS = ["AAPL", "MSFT", "GOOGL"]


def run_daily_report(out_dir: str = "reports", tickers=None) -> str:
    """
    Generates a daily CSV report for the portfolio and saves it into /reports.
    """
    tickers = tickers or DEFAULT_TICKERS

    prices = get_prices(tickers, period="2y", interval="1d")
    if prices is None or prices.empty:
        raise RuntimeError("No market data returned (prices empty).")

    # Equal-weight by default (weights=None in our backtester)
    res = backtest_portfolio(prices=prices, weights=None, initial_value=100.0, rebalance="Monthly")

    port_rets = portfolio_daily_returns(res.portfolio_value)

    report = {
        "timestamp_utc": datetime.utcnow().isoformat(),
        "tickers": ",".join(tickers),
        "last_date": str(res.portfolio_value.index[-1].date()),
        "portfolio_last_value": float(res.portfolio_value.iloc[-1]),
        "ann_return": annualized_return(res.portfolio_value),
        "ann_vol": annualized_vol(port_rets),
        "sharpe": sharpe_ratio(port_rets),
        "max_drawdown": max_drawdown(res.portfolio_value),
    }

    os.makedirs(out_dir, exist_ok=True)
    filename = f"portfolio_report_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    path = os.path.join(out_dir, filename)

    pd.DataFrame([report]).to_csv(path, index=False)
    return path


if __name__ == "__main__":
    path = run_daily_report()
    print("Report written to:", path)
