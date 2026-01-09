from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import pandas as pd

from src.data.market_data import get_prices
from src.portfolio.backtest import backtest_portfolio
from src.portfolio.metrics import (annualized_return, annualized_vol, max_drawdown, portfolio_daily_returns, sharpe_ratio,)


DEFAULT_TICKERS = ["AAPL", "MSFT", "GOOGL"]


def run_daily_report(tickers: Optional[List[str]] = None, out_dir: str = "reports") -> Path:
    """Create a daily CSV report with portfolio metrics and save it in /reports."""
    tickers = tickers or DEFAULT_TICKERS

    prices = get_prices(tickers, period="2y", interval="1d")
    if prices.empty:
        # No data -> no report
        return Path()

    result = backtest_portfolio(prices=prices, weights=None, initial_value=100.0, rebalance="Monthly")
    if result.portfolio_value.empty:
        return Path()

    port_rets = portfolio_daily_returns(result.portfolio_value)

    now_utc = datetime.now(timezone.utc)
    report = {"timestamp_utc": now_utc.isoformat(timespec="seconds"), "tickers": ",".join(tickers), "last_date": str(result.portfolio_value.index[-1].date()), "portfolio_last_value": float(result.portfolio_value.iloc[-1]), "ann_return": annualized_return(result.portfolio_value), "ann_vol": annualized_vol(port_rets), "sharpe": sharpe_ratio(port_rets), "max_drawdown": max_drawdown(result.portfolio_value),}

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    filename = f"portfolio_report_{now_utc.strftime('%Y%m%d')}.csv"
    file_path = out_path / filename

    pd.DataFrame([report]).to_csv(file_path, index=False)
    return file_path


if __name__ == "__main__":
    path = run_daily_report()
    if path:
        print("Report written to:", path)
    else:
        print("No report generated (missing data).")
