import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Quant Dashboard - AAPL", layout="wide")
st.title("Quant Dashboard - AAPL")

csv_path = os.path.join("data", "aapl_prices.csv")
if not os.path.exists(csv_path):
    st.error("Pas de données encore. Attends la collecte cron.")
    st.stop()

df = pd.read_csv(csv_path)
df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
df = df.sort_values("timestamp_utc")

last_ts = df["timestamp_utc"].iloc[-1]
last_price = df["price"].iloc[-1]

c1, c2, c3 = st.columns(3)
c1.metric("Dernier prix AAPL", f"{last_price:.4f}")
c2.metric("Dernier timestamp (UTC)", str(last_ts))
c3.metric("Nombre de points", str(len(df)))

st.subheader("Courbe du prix")
st.line_chart(df.set_index("timestamp_utc")["price"])

st.subheader("Dernières lignes")
st.dataframe(df.tail(20), use_container_width=True)

