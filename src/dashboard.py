import os
import numpy as np
import pandas as pd
import streamlit as st

from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Quant Dashboard - AAPL", layout="wide")

# Auto-refresh Streamlit (sans recharger toute la page HTML)
st_autorefresh(interval=300_000, key="refresh")  # 5 minutes

st.title("Quant Dashboard - AAPL")

# Chemins absolus (robuste même si lancé depuis un autre dossier)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(BASE_DIR, "data", "aapl_prices.csv")


@st.cache_data(ttl=300)
def load_prices(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required_cols = {"timestamp_utc", "price"}
    if not required_cols.issubset(set(df.columns)):
        raise ValueError(f"CSV invalide. Attendu: {required_cols}, reçu: {set(df.columns)}")

    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["timestamp_utc", "price"]).copy()

    # Dédupe + tri (important si history + cron écrivent)
    df = df.drop_duplicates(subset=["timestamp_utc"]).sort_values("timestamp_utc")
    return df


if not os.path.exists(csv_path):
    st.error("Pas de données encore. Lance `python -u src/app.py history` puis attends cron.")
    st.stop()

try:
    df = load_prices(csv_path)
except Exception as e:
    st.error(f"Impossible de lire le CSV: {e}")
    st.stop()

if len(df) < 2:
    st.warning("Pas assez de points (min 2) pour calculer des rendements/stratégies.")
    st.dataframe(df, width="stretch")
    st.stop()

df = df.set_index("timestamp_utc")

# Controls (periodicity + strategy)
colA, colB, colC = st.columns([1, 1, 2])
with colA:
    periodicity = st.selectbox("Périodicité", ["Raw", "15min", "1H", "1D"], index=0)
with colB:
    strategy = st.selectbox("Stratégie", ["Buy & Hold", "Momentum"], index=0)
with colC:
    mom_window = st.slider("Momentum window (N périodes)", min_value=2, max_value=50, value=10, step=1)

# Resample if needed
if periodicity == "Raw":
    s = df["price"].copy()
else:
    rule = {"15min": "15min", "1H": "1H", "1D": "1D"}[periodicity]
    s = df["price"].resample(rule).last().dropna()

if len(s) < 3:
    st.warning("Pas assez de points après resampling. Choisis une périodicité plus fine.")
    st.stop()

# Returns
ret = s.pct_change().fillna(0.0)

# Strategy returns
if strategy == "Buy & Hold":
    strat_ret = ret.copy()
else:
    # Momentum: on investit si la perf sur N périodes précédentes est > 0
    mom = s.pct_change(mom_window)
    position = (mom.shift(1) > 0).astype(float)  # éviter look-ahead
    strat_ret = (position * ret).fillna(0.0)

# Equity curve (cumulative value)
equity = (1.0 + strat_ret).cumprod()
equity_value = equity * float(s.iloc[0])  # démarre au même niveau que le prix

# Metrics helpers
def max_drawdown(series: pd.Series) -> float:
    running_max = series.cummax()
    dd = (series / running_max) - 1.0
    return float(dd.min())

def infer_periods_per_year(index: pd.DatetimeIndex) -> float:
    # approx basé sur le pas médian (fonctionne même si collecte 24/7)
    diffs = index.to_series().diff().dropna().dt.total_seconds()
    if len(diffs) == 0:
        return 0.0
    dt = float(diffs.median())
    if dt <= 0:
        return 0.0
    return (365.0 * 24.0 * 3600.0) / dt

ppy = infer_periods_per_year(s.index)
mean_r = float(strat_ret.mean())
std_r = float(strat_ret.std(ddof=0))

sharpe = (mean_r / std_r * np.sqrt(ppy)) if (std_r > 0 and ppy > 0) else float("nan")
tot_return = float(equity.iloc[-1] - 1.0)
mdd = max_drawdown(equity)
vol = (std_r * np.sqrt(ppy)) if (std_r > 0 and ppy > 0) else float("nan")

# Header KPIs
last_ts = s.index[-1]
last_price = float(s.iloc[-1])

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Dernier prix AAPL", f"{last_price:.4f}")
k2.metric("Dernier timestamp (UTC)", str(last_ts))
k3.metric("Nb points (après périodicité)", str(len(s)))
k4.metric("Total return (strat)", f"{tot_return*100:.2f}%")
k5.metric("Max drawdown", f"{mdd*100:.2f}%")

# Petite aide debug si le prix ne bouge pas
if s.nunique() <= 2:
    st.info("Le prix bouge très peu sur la fenêtre affichée → retour/vol/Sharpe peuvent rester faibles.")

st.caption(
    "Note: Sharpe/vol annualisés = approximation car la collecte se fait en continu (y compris hors marché)."
)

m1, m2 = st.columns(2)
m1.metric("Sharpe (approx)", "—" if np.isnan(sharpe) else f"{sharpe:.2f}")
m2.metric("Vol annualisée (approx)", "—" if np.isnan(vol) else f"{vol*100:.2f}%")

# Main chart
plot_df = pd.DataFrame(
    {
        "Price (raw)": s,
        "Strategy cumulative value": equity_value,
    }
)

st.subheader("Graph principal (prix brut + valeur cumulée stratégie)")
st.line_chart(plot_df)

st.subheader("Dernières lignes (après périodicité)")
tail_df = pd.DataFrame(
    {
        "price": s,
        "return": ret,
        "strategy_return": strat_ret,
        "equity_value": equity_value,
    }
).tail(30)
st.dataframe(tail_df, width="stretch")

st.caption(f"Fichier utilisé: {csv_path}")
