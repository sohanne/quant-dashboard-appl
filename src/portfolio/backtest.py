from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    prices: pd.DataFrame
    returns: pd.DataFrame
    portfolio_value: pd.Series
    weights_history: pd.DataFrame  # daily weights actually held (after drift + rebalance)


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Simple daily returns."""
    if prices is None or prices.empty:
        return pd.DataFrame()
    rets = prices.pct_change().replace([np.inf, -np.inf], np.nan).dropna(how="all")
    return rets


def normalize_weights(weights: Dict[str, float], tickers: List[str]) -> Dict[str, float]:
    """Ensure weights cover tickers and sum to 1."""
    w = {t: float(weights.get(t, 0.0)) for t in tickers}
    s = sum(w.values())
    if s <= 0:
        # fallback equal weight
        n = len(tickers)
        return {t: 1.0 / n for t in tickers}
    return {t: v / s for t, v in w.items()}


def _rebalance_dates(index: pd.DatetimeIndex, freq: str) -> pd.DatetimeIndex:
    """
    freq:
      - "Never" : no rebalance
      - "Weekly" : Mondays
      - "Monthly" : first business day of month
      - "Quarterly" : first business day of quarter
    """
    if len(index) == 0:
        return index

    if freq == "Never":
        return pd.DatetimeIndex([])

    idx = pd.DatetimeIndex(index).sort_values()
    if freq == "Weekly":
        # Mondays present in the index
        return idx[idx.weekday == 0]
    if freq == "Monthly":
        grp = pd.Series(1, index=idx).groupby([idx.year, idx.month]).head(1)
        return grp.index
    if freq == "Quarterly":
        q = ((idx.month - 1) // 3) + 1
        grp = pd.Series(1, index=idx).groupby([idx.year, q]).head(1)
        return grp.index

    # default: no rebalance
    return pd.DatetimeIndex([])


def backtest_portfolio(
    prices: pd.DataFrame,
    weights: Optional[Dict[str, float]] = None,
    initial_value: float = 100.0,
    rebalance: str = "Monthly",
) -> BacktestResult:
    """
    Simulate a drifting portfolio with optional rebalancing.
    - prices: DataFrame of adjusted close prices, columns=tickers, index=dates
    - weights: dict {ticker: weight}. If None -> equal weights.
    - rebalance: "Never" | "Weekly" | "Monthly" | "Quarterly"
    """
    if prices is None or prices.empty:
        return BacktestResult(
            prices=pd.DataFrame(),
            returns=pd.DataFrame(),
            portfolio_value=pd.Series(dtype=float),
            weights_history=pd.DataFrame(),
        )

    prices = prices.sort_index().dropna(how="all")
    prices = prices.dropna(axis=1, how="all")
    tickers = list(prices.columns)

    # compute returns
    rets = compute_returns(prices)

    # align prices to returns index (returns start after pct_change)
    prices_bt = prices.loc[rets.index]

    # target weights
    if weights is None:
        target_w = {t: 1.0 / len(tickers) for t in tickers}
    else:
        target_w = normalize_weights(weights, tickers)

    # initial holdings in "value terms"
    portfolio_value = pd.Series(index=prices_bt.index, dtype=float)
    weights_hist = pd.DataFrame(index=prices_bt.index, columns=tickers, dtype=float)

    # Start on first return date
    t0 = prices_bt.index[0]
    holdings_value = pd.Series({t: initial_value * target_w[t] for t in tickers}, dtype=float)

    rebalance_dates = set(_rebalance_dates(prices_bt.index, rebalance).to_pydatetime())

    prev_date = None
    for dt in prices_bt.index:
        if prev_date is None:
            # first day: just record
            pv = float(holdings_value.sum())
            portfolio_value.loc[dt] = pv
            weights_hist.loc[dt] = (holdings_value / pv).values
            prev_date = dt
            continue

        # drift holdings with returns from prev_date -> dt (use returns at dt)
        r = rets.loc[dt].fillna(0.0)
        holdings_value = holdings_value * (1.0 + r)

        # rebalance if needed
        if dt.to_pydatetime() in rebalance_dates:
            pv = float(holdings_value.sum())
            holdings_value = pd.Series({t: pv * target_w[t] for t in tickers}, dtype=float)

        pv = float(holdings_value.sum())
        portfolio_value.loc[dt] = pv
        weights_hist.loc[dt] = (holdings_value / pv).values
        prev_date = dt

    return BacktestResult(
        prices=prices_bt,
        returns=rets,
        portfolio_value=portfolio_value,
        weights_history=weights_hist,
    )
