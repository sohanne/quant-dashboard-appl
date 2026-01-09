from __future__ import annotations

from typing import Dict, List

import pandas as pd
import streamlit as st

from data.market_data import get_prices
from portfolio.backtest import backtest_portfolio
from portfolio.metrics import (annualized_return, annualized_vol, correlation_matrix, diversification_effect, max_drawdown, portfolio_daily_returns, sharpe_ratio,)
from portfolio.plots import plot_corr_heatmap, plot_cum_returns, plot_prices_and_portfolio


ASSET_UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
    "SPY", "QQQ", "GLD", "BTC-USD", "ETH-USD",
]


@st.cache_data(ttl=300, show_spinner=False)  # refresh every 5 minutes
def cached_prices(tickers: List[str], period: str) -> pd.DataFrame:
    return get_prices(tickers, period=period, interval="1d")


def render_portfolio_page() -> None:
    st.title("Quant Dashboard — Portfolio (Quant B)")
    st.subheader("Multi-Asset Portfolio")

    #Inputs
    tickers = st.multiselect("Choose at least 3 assets", options=ASSET_UNIVERSE, default=["AAPL", "MSFT", "GOOGL"],)

    if len(tickers) < 3:
        st.warning("Select at least 3 assets to build the portfolio.")
        return

    period = st.selectbox("Data window", ["6mo", "1y", "2y", "5y"], index=2)
    rebalance = st.selectbox("Rebalancing", ["Never", "Weekly", "Monthly", "Quarterly"], index=2)

    weight_mode = st.radio("Weights", ["Equal", "Custom"], horizontal=True)

    #Weights
    weights: Dict[str, float] = {}
    if weight_mode == "Equal":
        w = 1.0 / len(tickers)
        weights = {t: w for t in tickers}
        st.caption(f"Equal weights: {w*100:.2f}% per asset")
    else:
        cols = st.columns(min(4, len(tickers)))
        raw: Dict[str, float] = {}

        for i, t in enumerate(tickers):
            with cols[i % len(cols)]:
                raw[t] = st.slider(t, min_value=0.0, max_value=100.0, value=round(100.0 / len(tickers), 2), step=0.5,)

        s = sum(raw.values())
        if s <= 0:
            weights = {t: 1.0 / len(tickers) for t in tickers}
        else:
            weights = {t: raw[t] / s for t in tickers}

        weights_df = pd.DataFrame(
            {"Ticker": list(weights.keys()), "Weight (%)": [round(v * 100, 2) for v in weights.values()]}
        )
        st.dataframe(weights_df, use_container_width=True)

    st.divider()

    #Data
    with st.spinner("Downloading prices..."):
        prices = cached_prices(tickers, period=period)

    if prices is None or prices.empty:
        st.error("No data returned. Try different tickers or a different time window.")
        return

    #Backtest
    res = backtest_portfolio(prices=prices, weights=weights, initial_value=100.0, rebalance=rebalance)

    if res.portfolio_value.empty:
        st.error("Backtest failed (empty results).")
        return

    #Metrics
    port_rets = portfolio_daily_returns(res.portfolio_value)

    ann_ret = annualized_return(res.portfolio_value)
    ann_vol = annualized_vol(port_rets)
    sharpe = sharpe_ratio(port_rets)
    mdd = max_drawdown(res.portfolio_value)

    corr = correlation_matrix(res.returns)
    cov = res.returns.cov() * 252 if not res.returns.empty else pd.DataFrame()

    last_w = res.weights_history.iloc[-1] if not res.weights_history.empty else pd.Series(weights)
    div_eff = diversification_effect(last_w, cov) if not cov.empty else float("nan")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Ann. Return", f"{ann_ret*100:.2f}%")
    c2.metric("Ann. Vol", f"{ann_vol*100:.2f}%")
    c3.metric("Sharpe", f"{sharpe:.2f}")
    c4.metric("Max Drawdown", f"{mdd*100:.2f}%")
    c5.metric("Diversification", f"{div_eff:.4f}")

    st.divider()

    #Charts
    st.plotly_chart(plot_prices_and_portfolio(res.prices, res.portfolio_value), use_container_width=True)
    st.plotly_chart(plot_cum_returns(res.returns, port_rets), use_container_width=True)
    st.plotly_chart(plot_corr_heatmap(corr), use_container_width=True)
