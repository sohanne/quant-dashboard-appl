from __future__ import annotations

from typing import Dict, List

import pandas as pd
import streamlit as st

from data.market_data import get_prices
from portfolio.backtest import backtest_portfolio
from portfolio.metrics import (
    annualized_return,
    annualized_vol,
    correlation_matrix,
    diversification_effect,
    max_drawdown,
    portfolio_daily_returns,
    sharpe_ratio,
)
from portfolio.plots import plot_corr_heatmap, plot_cum_returns, plot_prices_and_portfolio


@st.cache_data(ttl=300, show_spinner=False)  # 5 minutes
def cached_prices(tickers: List[str], period: str) -> pd.DataFrame:
    return get_prices(tickers, period=period, interval="1d")


def _default_tickers() -> List[str]:
    return ["AAPL", "MSFT", "GOOGL"]


def render_portfolio_page():
    st.header("Quant B — Multi-Asset Portfolio")

    #Controls
    tickers = st.multiselect("Select at least 3 assets", options=[
        "AAPL","MSFT","GOOGL","AMZN","META","NVDA","TSLA","SPY","QQQ","GLD","BTC-USD","ETH-USD"
    ], default=_default_tickers())

    if len(tickers) < 3:
        st.warning("Please select at least 3 assets (project requirement).")
        return

    period = st.selectbox("Data window", ["6mo", "1y", "2y", "5y"], index=2)
    rebalance = st.selectbox("Rebalancing frequency", ["Never", "Weekly", "Monthly", "Quarterly"], index=2)

    weight_mode = st.radio("Weights", ["Equal weight", "Custom weights"], horizontal=True)

    weights: Dict[str, float] = {}
    if weight_mode == "Equal weight":
        w = 1.0 / len(tickers)
        weights = {t: w for t in tickers}
        st.caption(f"Equal weights: {round(w*100,2)}% each")
    else:
        st.caption("Tip: set any weights — they will be normalized to sum to 100%.")
        cols = st.columns(min(4, len(tickers)))
        raw = {}
        for i, t in enumerate(tickers):
            with cols[i % len(cols)]:
                raw[t] = st.slider(f"{t}", min_value=0.0, max_value=100.0, value=round(100.0/len(tickers), 2), step=0.5)
        s = sum(raw.values())
        if s <= 0:
            weights = {t: 1.0 / len(tickers) for t in tickers}
        else:
            weights = {t: raw[t] / s for t in tickers}

        st.write("Normalized weights (%)")
        st.dataframe(pd.DataFrame({"ticker": list(weights.keys()), "weight_%": [round(v*100,2) for v in weights.values()]}))

    st.divider()

    #Data
    with st.spinner("Fetching market data..."):
        prices = cached_prices(tickers, period=period)

    if prices is None or prices.empty:
        st.error("Data source returned no data. Please try again later or change tickers/period.")
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

    #Plots required: prices + portfolio value; plus comparison assets vs portfolio
    st.plotly_chart(plot_prices_and_portfolio(res.prices, res.portfolio_value), use_container_width=True)
    st.plotly_chart(plot_cum_returns(res.returns, port_rets), use_container_width=True)

    heat = plot_corr_heatmap(corr)
    if heat is not None:
        st.plotly_chart(heat, use_container_width=True)
