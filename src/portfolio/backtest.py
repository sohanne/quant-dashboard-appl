from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    prices: pd.DataFrame
    returns: pd.DataFrame
    portfolio_value: pd.Series
    weights_history: pd.DataFrame  # daily weights held 


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Compute simple daily returns from a price DataFrame."""
    if prices is None or prices.empty:
        return pd.DataFrame()

    rets = prices.pct_change()
    rets = rets.replace([np.inf, -np.inf], np.nan).dropna(how="all")
    return rets


def normalize_weights(weights: Dict[str, float], tickers: List[str]) -> Dict[str, float]:
    """Normalize user weights so they cover all tickers and sum to 1."""
    w = {t: float(weights.get(t, 0.0)) for t in tickers}
    s = sum(w.values())

    if s <= 0:
        # fallback: equal-weight
        n = len(tickers)
        return {t: 1.0 / n for t in tickers}

    return {t: v / s for t, v in w.items()}


def rebalance_dates(index: pd.DatetimeIndex, freq: str) -> pd.DatetimeIndex:
    """
    Return the dates where we rebalance.
    freq can be: "Never", "Weekly", "Monthly", "Quarterly"
    """
    if index is None or len(index) == 0:
        return pd.DatetimeIndex([])

    idx = pd.DatetimeIndex(index).sort_values()

    if freq == "Never":
        return pd.DatetimeIndex([])

    if freq == "Weekly":
        # Mondays in the index
        return idx[idx.weekday == 0]

    if freq == "Monthly":
        # first available date of each month
        return idx.to_series().groupby([idx.year, idx.month]).head(1).index

    if freq == "Quarterly":
        q = ((idx.month - 1) // 3) + 1
        return idx.to_series().groupby([idx.year, q]).head(1).index

    # default
    return pd.DatetimeIndex([])


def backtest_portfolio(prices: pd.DataFrame, weights: Optional[Dict[str, float]] = None, initial_value: float = 100.0, rebalance: str = "Monthly",) -> BacktestResult:
    """
    Simple portfolio backtest:
    - drift daily using asset returns
    - optionally rebalance at a chosen frequency
    """
    if prices is None or prices.empty:
        return BacktestResult(prices=pd.DataFrame(),returns=pd.DataFrame(), portfolio_value=pd.Series(dtype=float), weights_history=pd.DataFrame(),)

    # Clean input
    prices = prices.sort_index().dropna(how="all").dropna(axis=1, how="all")
    tickers = list(prices.columns)

    # Returns start at t1 (after pct_change)
    rets = compute_returns(prices)
    if rets.empty:
        return BacktestResult(prices=pd.DataFrame(), returns=pd.DataFrame(), portfolio_value=pd.Series(dtype=float), weights_history=pd.DataFrame(),)

    prices_bt = prices.loc[rets.index]

    # Target weights
    if weights is None:
        target_w = {t: 1.0 / len(tickers) for t in tickers}
    else:
        target_w = normalize_weights(weights, tickers)

    # Prepare outputs
    portfolio_value = pd.Series(index=prices_bt.index, dtype=float)
    weights_hist = pd.DataFrame(index=prices_bt.index, columns=tickers, dtype=float)

    # Start: allocate initial value by target weights
    holdings = pd.Series({t: initial_value * target_w[t] for t in tickers}, dtype=float)

    rb_dates = set(rebalance_dates(prices_bt.index, rebalance))

    for i, dt in enumerate(prices_bt.index):
        if i == 0:
            pv = float(holdings.sum())
            portfolio_value.loc[dt] = pv
            weights_hist.loc[dt] = (holdings / pv).values
            continue

        # Drift holdings using daily returns
        r = rets.loc[dt].fillna(0.0)
        holdings = holdings * (1.0 + r)

        # Rebalance if needed
        if dt in rb_dates:
            pv = float(holdings.sum())
            holdings = pd.Series({t: pv * target_w[t] for t in tickers}, dtype=float)

        pv = float(holdings.sum())
        portfolio_value.loc[dt] = pv
        weights_hist.loc[dt] = (holdings / pv).values

    return BacktestResult(prices=prices_bt, returns=rets, portfolio_value=portfolio_value, weights_history=weights_hist,)

