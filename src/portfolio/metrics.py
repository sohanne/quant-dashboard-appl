from __future__ import annotations

import numpy as np
import pandas as pd


def max_drawdown(values: pd.Series) -> float:
    """Return the worst peak-to-trough drawdown of a portfolio value series."""
    if values is None or values.empty:
        return float("nan")

    running_max = values.cummax()
    drawdowns = (values / running_max) - 1.0
    return float(drawdowns.min())


def annualized_return(values: pd.Series, periods_per_year: int = 252) -> float:
    """Annualized return based on the portfolio value series. We assume values are equally spaced (daily data by default)."""
    if values is None or values.empty or len(values) < 2:
        return float("nan")

    total_growth = values.iloc[-1] / values.iloc[0]
    n_periods = len(values) - 1

    if total_growth <= 0:
        return float("nan")

    return float(total_growth ** (periods_per_year / n_periods) - 1.0)


def annualized_vol(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Annualized volatility from a series of periodic returns (daily by default)."""
    if returns is None or returns.empty:
        return float("nan")

    vol = returns.std(ddof=1)
    if np.isnan(vol):
        return float("nan")

    return float(vol * np.sqrt(periods_per_year))


def sharpe_ratio(returns: pd.Series, rf: float = 0.0, periods_per_year: int = 252) -> float:
    """Sharpe ratio (annualized). rf is expressed as an annual risk-free rate (e.g. 0.02 for 2%)."""
    if returns is None or returns.empty:
        return float("nan")

    # Convert annual rf to per-period rf
    excess = returns - (rf / periods_per_year)

    vol = excess.std(ddof=1)
    if vol == 0 or np.isnan(vol):
        return float("nan")

    return float((excess.mean() / vol) * np.sqrt(periods_per_year))


def portfolio_daily_returns(portfolio_value: pd.Series) -> pd.Series:
    """Compute daily returns from a portfolio value series."""
    if portfolio_value is None or portfolio_value.empty:
        return pd.Series(dtype=float)

    rets = portfolio_value.pct_change()
    rets = rets.replace([np.inf, -np.inf], np.nan).dropna()
    return rets


def correlation_matrix(asset_returns: pd.DataFrame) -> pd.DataFrame:
    """Correlation matrix between assets (based on returns)."""
    if asset_returns is None or asset_returns.empty:
        return pd.DataFrame()

    return asset_returns.corr()


def diversification_effect(weights: pd.Series, cov: pd.DataFrame) -> float:
    """Simple diversification score: weighted average individual vol - portfolio vol.
    If assets are not perfectly correlated, portfolio vol should be lower than the weighted average of individual vols, which gives a positive score."""
    if cov is None or cov.empty or weights is None or weights.empty:
        return float("nan")

    # Ensure order matches covariance matrix
    w = weights.reindex(cov.index).fillna(0.0).values

    indiv_vols = np.sqrt(np.diag(cov.values))
    port_var = float(w.T @ cov.values @ w)
    port_vol = float(np.sqrt(max(port_var, 0.0)))

    weighted_avg_vol = float(np.sum(np.abs(w) * indiv_vols))
    return float(weighted_avg_vol - port_vol)

