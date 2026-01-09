from __future__ import annotations

import numpy as np
import pandas as pd


def max_drawdown(series: pd.Series) -> float:
    if series is None or series.empty:
        return float("nan")
    cummax = series.cummax()
    dd = (series / cummax) - 1.0
    return float(dd.min())


def annualized_return(series: pd.Series, periods_per_year: int = 252) -> float:
    if series is None or series.empty:
        return float("nan")
    # series is portfolio value
    total = series.iloc[-1] / series.iloc[0]
    n = len(series)
    if n <= 1:
        return float("nan")
    return float(total ** (periods_per_year / (n - 1)) - 1.0)


def annualized_vol(returns: pd.Series, periods_per_year: int = 252) -> float:
    if returns is None or returns.empty:
        return float("nan")
    return float(returns.std(ddof=1) * np.sqrt(periods_per_year))


def sharpe_ratio(returns: pd.Series, rf: float = 0.0, periods_per_year: int = 252) -> float:
    if returns is None or returns.empty:
        return float("nan")
    excess = returns - (rf / periods_per_year)
    vol = excess.std(ddof=1)
    if vol == 0 or np.isnan(vol):
        return float("nan")
    return float((excess.mean() / vol) * np.sqrt(periods_per_year))


def portfolio_daily_returns(portfolio_value: pd.Series) -> pd.Series:
    if portfolio_value is None or portfolio_value.empty:
        return pd.Series(dtype=float)
    return portfolio_value.pct_change().replace([np.inf, -np.inf], np.nan).dropna()


def correlation_matrix(asset_returns: pd.DataFrame) -> pd.DataFrame:
    if asset_returns is None or asset_returns.empty:
        return pd.DataFrame()
    return asset_returns.corr()


def diversification_effect(weights: pd.Series, cov: pd.DataFrame) -> float:
    """
    Simple "diversification effect" idea:
    effect = sum(w_i * vol_i) - portfolio_vol
    """
    if cov is None or cov.empty or weights is None or weights.empty:
        return float("nan")

    # individual vols
    vols = np.sqrt(np.diag(cov))
    w = weights.reindex(cov.index).fillna(0.0).values
    port_var = float(w.T @ cov.values @ w)
    port_vol = np.sqrt(port_var)

    weighted_avg_vol = float(np.sum(np.abs(w) * vols))
    return float(weighted_avg_vol - port_vol)
