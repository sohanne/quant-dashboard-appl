import os
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Quant Dashboard - AAPL", layout="wide")
st_autorefresh(interval=300_000, key="refresh")

st.title("Quant Dashboard - AAPL")

# Chemins absolus
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(BASE_DIR, "data", "aapl_prices.csv")


@st.cache_data(ttl=300)
def load_prices(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    required_cols = {"timestamp_utc", "price"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"CSV invalide. Attendu: {required_cols}, reçu: {set(df.columns)}")

    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["timestamp_utc", "price"]).copy()

    # Dédupe + tri
    df = df.drop_duplicates(subset=["timestamp_utc"]).sort_values("timestamp_utc")
    return df


def infer_periods_per_year(index: pd.DatetimeIndex) -> float:
    diffs = index.to_series().diff().dropna().dt.total_seconds()
    if len(diffs) == 0:
        return 0.0
    dt = float(diffs.median())
    if dt <= 0:
        return 0.0
    return (365.0 * 24.0 * 3600.0) / dt


def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = equity / peak - 1.0
    return float(dd.min())


def drawdown_series(equity: pd.Series) -> pd.Series:
    peak = equity.cummax()
    return equity / peak - 1.0


def perf_metrics(ret: pd.Series, equity: pd.Series, ppy: float) -> dict:
    # ret: série de rendements périodiques
    mean_r = float(ret.mean())
    std_r = float(ret.std(ddof=0))
    tot_return = float(equity.iloc[-1] - 1.0)
    vol = (std_r * np.sqrt(ppy)) if (std_r > 0 and ppy > 0) else np.nan
    sharpe = (mean_r / std_r * np.sqrt(ppy)) if (std_r > 0 and ppy > 0) else np.nan
    mdd = max_drawdown(equity)

    win_rate = float((ret > 0).mean()) if len(ret) else np.nan

    return {
        "Total return": tot_return,
        "Vol (ann.)": vol,
        "Sharpe (ann.)": sharpe,
        "Max drawdown": mdd,
        "Win rate": win_rate,
    }


if not os.path.exists(csv_path):
    st.error("Pas de données encore. Lance `python -u src/app.py history` puis attends cron.")
    st.stop()

try:
    df = load_prices(csv_path)
except Exception as e:
    st.error(f"Impossible de lire le CSV: {e}")
    st.stop()

if len(df) < 3:
    st.warning("Pas assez de points (min 3).")
    st.dataframe(df, width="stretch")
    st.stop()

df = df.set_index("timestamp_utc").sort_index()

# -----------------------
# Controls
# -----------------------
top1, top2, top3, top4 = st.columns([1, 1, 1, 2])
with top1:
    periodicity = st.selectbox("Périodicité", ["Raw", "15min", "1H", "1D"], index=0)
with top2:
    mom_window = st.slider("Momentum window (N périodes)", min_value=2, max_value=200, value=20, step=1)
with top3:
    log_scale = st.checkbox("Échelle log (graph principal)", value=False)
with top4:
    fee_bps = st.number_input("Frais (bps) appliqués aux trades Momentum", min_value=0.0, max_value=200.0, value=0.0, step=1.0)

# Date range (UTC)
min_dt = df.index.min().date()
max_dt = df.index.max().date()
dcol1, dcol2 = st.columns(2)
with dcol1:
    start_date = st.date_input("Date début (UTC)", value=min_dt, min_value=min_dt, max_value=max_dt)
with dcol2:
    end_date = st.date_input("Date fin (UTC)", value=max_dt, min_value=min_dt, max_value=max_dt)

if start_date > end_date:
    st.error("La date début doit être <= date fin.")
    st.stop()

mask = (df.index.date >= start_date) & (df.index.date <= end_date)
dfw = df.loc[mask].copy()

if len(dfw) < 3:
    st.warning("Pas assez de points sur la fenêtre sélectionnée.")
    st.stop()

# Resample
if periodicity == "Raw":
    s = dfw["price"].copy()
else:
    rule = {"15min": "15min", "1H": "1H", "1D": "1D"}[periodicity]
    s = dfw["price"].resample(rule).last().dropna()

if len(s) < max(10, mom_window + 2):
    st.warning("Pas assez de points après resampling / pour la fenêtre momentum. Réduis N ou choisis une périodicité plus fine.")
    st.stop()

# -----------------------
# Returns & strategies
# -----------------------
ret = s.pct_change().fillna(0.0)

# Buy & Hold
bh_ret = ret.copy()

# Momentum (long/flat) : investi si perf sur N périodes précédentes > 0 (avec shift pour éviter look-ahead)
mom_raw = s.pct_change(mom_window)
position = (mom_raw.shift(1) > 0).astype(float)  # 1.0 ou 0.0
mom_ret_gross = (position * ret).fillna(0.0)

# Frais sur changement de position (trades)
# fee_bps = basis points, ex: 10 bps = 0.001
fee = fee_bps / 10_000.0
turnover = position.diff().abs().fillna(0.0)  # 1 quand on entre/sort (approx)
mom_ret = mom_ret_gross - turnover * fee

# Equity curves normalisées (base = 1)
bh_equity = (1.0 + bh_ret).cumprod()
mom_equity = (1.0 + mom_ret).cumprod()
price_norm = s / float(s.iloc[0])

# Drawdowns
bh_dd = drawdown_series(bh_equity)
mom_dd = drawdown_series(mom_equity)

# Annualisation approx
ppy = infer_periods_per_year(s.index)

# Metrics
bh_m = perf_metrics(bh_ret, bh_equity, ppy)
mom_m = perf_metrics(mom_ret, mom_equity, ppy)

# Extra momentum metrics
nb_trades = int((position.diff().abs() > 0).sum())
mom_m["# Trades (approx)"] = nb_trades
bh_m["# Trades (approx)"] = 0

metrics_df = pd.DataFrame([bh_m, mom_m], index=["Buy & Hold", "Momentum"])

# Pretty formatting
fmt = metrics_df.copy()
for c in ["Total return", "Vol (ann.)", "Max drawdown", "Win rate"]:
    if c in fmt.columns:
        fmt[c] = fmt[c].apply(lambda x: "—" if pd.isna(x) else f"{x*100:.2f}%")
if "Sharpe (ann.)" in fmt.columns:
    fmt["Sharpe (ann.)"] = fmt["Sharpe (ann.)"].apply(lambda x: "—" if pd.isna(x) else f"{x:.2f}")

# KPIs header
last_ts = s.index[-1]
last_price = float(s.iloc[-1])

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Dernier prix AAPL", f"{last_price:.4f}")
k2.metric("Dernier timestamp (UTC)", str(last_ts))
k3.metric("Nb points (après périodicité)", str(len(s)))
k4.metric("Momentum: position actuelle", "1 (IN)" if position.iloc[-1] > 0 else "0 (OUT)")
k5.metric("Frais (bps)", f"{fee_bps:.1f}")

st.caption("Note: annualisation = approximation (collecte potentiellement 24/7).")

# -----------------------
# Charts (Plotly)
# -----------------------
fig = make_subplots(
    rows=3, cols=1, shared_xaxes=True,
    vertical_spacing=0.07,
    row_heights=[0.55, 0.25, 0.20],
    subplot_titles=(
        "Prix normalisé vs Equity curves (Buy & Hold & Momentum)",
        "Drawdown (B&H vs Momentum)",
        "Position Momentum (0/1)"
    )
)

# Row 1: price + equities
fig.add_trace(go.Scatter(x=s.index, y=price_norm, name="Price (norm)", mode="lines"), row=1, col=1)
fig.add_trace(go.Scatter(x=s.index, y=bh_equity, name="Buy & Hold (equity)", mode="lines"), row=1, col=1)
fig.add_trace(go.Scatter(x=s.index, y=mom_equity, name="Momentum (equity)", mode="lines"), row=1, col=1)

# Row 2: drawdowns
fig.add_trace(go.Scatter(x=s.index, y=bh_dd, name="B&H drawdown", mode="lines"), row=2, col=1)
fig.add_trace(go.Scatter(x=s.index, y=mom_dd, name="Momentum drawdown", mode="lines"), row=2, col=1)

# Row 3: position (step-like)
fig.add_trace(go.Scatter(
    x=s.index, y=position,
    name="Momentum position",
    mode="lines",
    line=dict(shape="hv")
), row=3, col=1)

fig.update_layout(
    height=850,
    margin=dict(l=20, r=20, t=60, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
)

if log_scale:
    fig.update_yaxes(type="log", row=1, col=1)

fig.update_yaxes(tickformat=".2f", row=1, col=1)
fig.update_yaxes(tickformat=".0%", row=2, col=1)
fig.update_yaxes(range=[-0.05, 1.05], row=3, col=1)

st.subheader("Comparaison visuelle des stratégies")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Métriques comparatives")
st.dataframe(fmt, width="stretch")

# Debug / table récente
tail_df = pd.DataFrame({
    "price": s,
    "ret": ret,
    "bh_ret": bh_ret,
    "mom_signal": mom_raw,
    "position": position,
    "mom_ret_net": mom_ret,
    "bh_equity": bh_equity,
    "mom_equity": mom_equity,
}).tail(50)

with st.expander("Voir les dernières lignes (debug)", expanded=False):
    st.dataframe(tail_df, width="stretch")

st.caption(f"Fichier utilisé: {csv_path}")
