from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def plot_prices_and_portfolio(prices: pd.DataFrame, portfolio_value: pd.Series) -> go.Figure:
    """Plot asset price series and the portfolio value on the same chart."""
    fig = go.Figure()

    if prices is not None and not prices.empty:
        for ticker in prices.columns:
            fig.add_trace(
                go.Scatter(x=prices.index, y=prices[ticker], mode="lines", name=str(ticker))
            )

    if portfolio_value is not None and not portfolio_value.empty:
        fig.add_trace(go.Scatter(x=portfolio_value.index, y=portfolio_value.values, mode="lines", name="Portfolio Value",))

    fig.update_layout(title="Asset Prices + Portfolio Value", xaxis_title="Date", yaxis_title="Price / Value", legend_title="Series", height=520,)
    return fig


def plot_cum_returns(asset_returns: pd.DataFrame, portfolio_returns: pd.Series) -> go.Figure:
    """Plot cumulative performance (growth of $1) for assets and portfolio."""
    fig = go.Figure()

    if asset_returns is not None and not asset_returns.empty:
        cum_assets = (1.0 + asset_returns).cumprod()
        for ticker in cum_assets.columns:
            fig.add_trace(go.Scatter(x=cum_assets.index, y=cum_assets[ticker], mode="lines", name=f"{ticker} (cum)",))

    if portfolio_returns is not None and not portfolio_returns.empty:
        cum_port = (1.0 + portfolio_returns).cumprod()
        fig.add_trace(
            go.Scatter(x=cum_port.index, y=cum_port.values, mode="lines", name="Portfolio (cum)")
        )

    fig.update_layout(title="Cumulative Performance: Assets vs Portfolio", xaxis_title="Date", yaxis_title="Cumulative Growth", height=520,)
    return fig


def plot_corr_heatmap(corr: pd.DataFrame) -> go.Figure:
    """Plot a correlation matrix as a heatmap."""
    if corr is None or corr.empty:
        return go.Figure()

    fig = go.Figure(data=go.Heatmap(z=corr.values, x=corr.columns.astype(str), y=corr.index.astype(str), zmin=-1, zmax=1,)
    )
    fig.update_layout(
        title="Correlation Matrix",
        height=520,
    )
    return fig
