import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

st.set_page_config(page_title="TIA/ALCH Tracker ByBit", layout="wide")
st.title("📊 TIA/ALCH – Live Tracker (USD, ByBit)")

@st.cache_data(ttl=300)
def fetch_price_data(symbol: str, limit: int = 168):
    url = "https://api.bybit.com/v5/market/kline"
    params = {"category": "spot", "symbol": symbol, "interval": "60", "limit": limit}
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data["result"]["list"], columns=[
        "timestamp", "open", "high", "low", "close", "volume", "turnover"
    ])
    df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit='ms')
    df["close"] = df["close"].astype(float)
    return df[["timestamp", "close"]].sort_values("timestamp").reset_index(drop=True)

tia_df = fetch_price_data("TIAUSDT")
alch_df = fetch_price_data("ALCHUSDT")

df = pd.merge(tia_df, alch_df, on="timestamp", suffixes=("_TIA", "_ALCH"))
df["ratio"] = df["close_TIA"] / df["close_ALCH"]
mean = df["ratio"].mean()
std = df["ratio"].std()
upper = mean + std
lower = mean - std

last_row = df.iloc[-1]
last_time = last_row["timestamp"]
last_ratio = last_row["ratio"]

if last_ratio > upper:
    signal = "🔴 Kup ALCH za TIA"
elif last_ratio < lower:
    signal = "🟢 Kup TIA za ALCH"
else:
    signal = "🟡 Trzymaj"

fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(df["timestamp"], df["ratio"], label="TIA/ALCH", color="orange")
ax.axhline(mean, linestyle="--", color="gray", label="Średnia")
ax.axhline(upper, linestyle="--", color="red", label="+1σ (kup ALCH)")
ax.axhline(lower, linestyle="--", color="green", label="-1σ (kup TIA)")
ax.plot(last_time, last_ratio, marker="o", color="blue", markersize=8, label="Aktualna wartość")
ax.set_title("Stosunek TIA/ALCH – dane ByBit")
ax.set_xlabel("Data")
ax.set_ylabel("Stosunek TIA/ALCH")
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
st.pyplot(fig)
st.markdown(f"### 📌 Obecny stosunek: **{last_ratio:.2f}** &nbsp;&nbsp;&nbsp; {signal}")