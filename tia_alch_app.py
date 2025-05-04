
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

st.set_page_config(page_title="TIA/ALCH – HTX", layout="wide")

if "tia" not in st.session_state:
    st.session_state.tia = 3151.87
if "alch" not in st.session_state:
    st.session_state.alch = 15117.82

def fetch_price_df(symbol_url):
    try:
        r = requests.get(symbol_url)
        r.raise_for_status()
        data = r.json()
        k = data.get("data") or data.get("result") or data.get("candles") or list(data.values())[0]
        df = pd.DataFrame(k)
        df["timestamp"] = pd.to_datetime(df.iloc[:, 0].astype(float), unit="s")
        df["close"] = df.iloc[:, 1].astype(float)
        return df[["timestamp", "close"]].sort_values("timestamp").tail(168)
    except Exception as e:
        st.error(f"Błąd pobierania danych z HTX: {e}")
        return pd.DataFrame(columns=["timestamp", "close"])

st.title("📊 TIA/ALCH – HTX")

tia_url = "https://api.huobi.pro/market/history/kline?symbol=tiausdt&period=60min&size=168"
alch_url = "https://api.huobi.pro/market/history/kline?symbol=alchusdt&period=60min&size=168"

tia_df = fetch_price_df(tia_url)
alch_df = fetch_price_df(alch_url)

if tia_df.empty or alch_df.empty:
    st.error("Brak danych historycznych.")
    st.stop()

df = pd.merge(tia_df, alch_df, on="timestamp", suffixes=("_TIA", "_ALCH"))
df["ratio"] = df["close_TIA"] / df["close_ALCH"]
df = df.sort_values("timestamp")

mean = df["ratio"].mean()
std = df["ratio"].std()
upper = mean + std
lower = mean - std
last = df.iloc[-1]
ratio = last["ratio"]
now = last["timestamp"]

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df["timestamp"], df["ratio"], label="TIA/ALCH", color="orange")
ax.axhline(mean, color="gray", linestyle="--", label="Średnia")
ax.axhline(upper, color="red", linestyle="--", label="+1σ (kup ALCH)")
ax.axhline(lower, color="green", linestyle="--", label="-1σ (kup TIA)")
ax.plot(now, ratio, "o", color="blue", label="Obecnie")
ax.legend()
st.pyplot(fig)

st.subheader("📌 Sygnał")
if ratio > upper and st.session_state.tia > 0:
    amt = st.session_state.tia * 0.25
    out = amt * ratio
    st.success("🔴 Sygnał: kup ALCH za TIA")
elif ratio < lower and st.session_state.alch > 0:
    amt = st.session_state.alch * 0.25
    out = amt / ratio
    st.success("🟢 Sygnał: kup TIA za ALCH")
else:
    st.info("🟡 Sygnał: trzymaj")