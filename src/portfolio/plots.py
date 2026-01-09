from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def plot_prices_and_portfolio(prices: pd.DataFrame, portfolio_value: pd.Series) -> go.Figure:
    fig = go.Figure()

    if prices is not None and not prices.empty:
        for col in prices.columns:
            fig.add_trace(go.Scatter(x=prices.index, y=prices[col], mode="lines", name=str(col)))

    if portfolio_value is not None and not portfolio_value.empty:
        fig.add_trace(go.Scatter(x=portfolio_value.index, y=portfolio_value.values, mode="lines", name="Portfolio Value"))

    fig.update_layout(
        title="Asset Prices + Portfolio Value",
        xaxis_title="Date",
        yaxis_title="Price / Value",
        legend_title="Series",
        height=520,
    )
    return fig


def plot_cum_returns(asset_returns: pd.DataFrame, portfolio_returns: pd.Series) -> go.Figure:
    fig = go.Figure()

    if asset_returns is not None and not asset_returns.empty:
        cum = (1 + asset_returns).cumprod()
        for col in cum.columns:
            fig.add_trace(go.Scatter(x=cum.index, y=cum[col], mode="lines", name=f"{col} (cum)"))

    if portfolio_returns is not None and not portfolio_returns.empty:
        p_cum = (1 + portfolio_returns).cumprod()
        fig.add_trace(go.Scatter(x=p_cum.index, y=p_cum.values, mode="lines", name="Portfolio (cum)"))

    fig.update_layout(
        title="Cumulative Performance: Assets vs Portfolio",
        xaxis_title="Date",
        yaxis_title="Cumulative Growth",
        height=520,
    )
    return fig


def plot_corr_heatmap(corr: pd.DataFrame):
    if corr is None or corr.empty:
        return None
    fig = px.imshow(
        corr,
        text_auto=True,
        aspect="auto",
        title="Correlation Matrix",
    )
    fig.update_layout(height=520)
    return fig
