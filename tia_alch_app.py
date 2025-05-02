
# TIA/ALCH App v7 – z aktualnym stanem portfela i logiczną strategią zamiany

import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
from datetime import datetime

# Stan portfela po ostatniej transakcji
wallet = {
    "TIA": 4202.48 - 1050.61,  # pozostało po konwersji
    "ALCH": 15117.82           # otrzymane z wymiany
}

# Konfiguracja API
API_URL = "https://api.bybit.com/v5/market/kline"

@st.cache_data(ttl=300)
def fetch_price_data(symbol: str, limit: int = 168):
    params = {
        "category": "spot",
        "symbol": symbol,
        "interval": "60",
        "limit": limit
    }
    try:
        response = requests.get(API_URL, params=params)
        data = response.json()
        df = pd.DataFrame(data["result"]["list"], columns=[
            "timestamp", "open", "high", "low", "close", "volume", "turnover"
        ])
        df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit='ms')
        df["close"] = df["close"].astype(float)
        return df[["timestamp", "close"]].sort_values("timestamp").reset_index(drop=True)
    except:
        return pd.DataFrame(columns=["timestamp", "close"])

# Pobieranie danych
st.set_page_config(page_title="TIA/ALCH Live Tracker", layout="wide")
st.title("📊 TIA/ALCH – Strategiczny Monitor Portfela")
tia_df = fetch_price_data("TIAUSDT")
alch_df = fetch_price_data("ALCHUSDT")

if tia_df.empty or alch_df.empty:
    st.error("Brak danych z ByBit – sprawdź połączenie API.")
    st.stop()

# Obliczenia
merged = pd.merge(tia_df, alch_df, on="timestamp", suffixes=("_TIA", "_ALCH"))
merged["ratio"] = merged["close_TIA"] / merged["close_ALCH"]
mean = merged["ratio"].mean()
std = merged["ratio"].std()
upper = mean + std
lower = mean - std

last = merged.iloc[-1]
last_ratio = last["ratio"]
last_time = last["timestamp"]

# Sygnał
if last_ratio > upper:
    signal = "🔴 Zamień część TIA na ALCH"
elif last_ratio < lower:
    signal = "🟢 Zamień część ALCH na TIA"
else:
    signal = "🟡 Trzymaj"

# Wykres
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(merged["timestamp"], merged["ratio"], label="TIA/ALCH", color="orange")
ax.axhline(mean, linestyle="--", color="gray", label="Średnia")
ax.axhline(upper, linestyle="--", color="red", label="+1σ")
ax.axhline(lower, linestyle="--", color="green", label="-1σ")
ax.plot(last_time, last_ratio, "o", color="blue", label="Obecnie")
ax.set_title("Stosunek TIA/ALCH z ByBit (1h)")
ax.legend()
ax.grid(True)
st.pyplot(fig)

# Interfejs portfela
st.markdown("### 💼 Stan portfela")
st.write(f"**TIA:** {wallet['TIA']:.2f}  ")
st.write(f"**ALCH:** {wallet['ALCH']:.2f}  ")

# Sygnał + sugestia
st.markdown("### 📌 Obecny sygnał")
st.success(signal)

# Sugestia działania
if "ALCH" in signal and wallet["ALCH"] > 0:
    alch_to_swap = wallet["ALCH"] * 0.25
    tia_recv = alch_to_swap / last_ratio
    st.info(f"Sugerowana konwersja: zamień {alch_to_swap:.2f} ALCH na ~{tia_recv:.2f} TIA")
elif "TIA" in signal and wallet["TIA"] > 0:
    tia_to_swap = wallet["TIA"] * 0.25
    alch_recv = tia_to_swap * last_ratio
    st.info(f"Sugerowana konwersja: zamień {tia_to_swap:.2f} TIA na ~{alch_recv:.2f} ALCH")
else:
    st.info("Obecnie brak zalecanej akcji – obserwuj rynek.")

st.caption(f"Dane z ByBit • Aktualizacja: {last_time.strftime('%Y-%m-%d %H:%M')} • Stosunek: {last_ratio:.2f}")
