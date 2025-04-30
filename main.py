# TIA/ALCH Streamlit App (v2) - z aktualizacją co minutę, lepszym UI i strategiami

import streamlit as st
import pandas as pd
import requests
import time
import plotly.graph_objs as go
from datetime import datetime

# === Ustawienia ===
st.set_page_config(page_title="TIA/ALCH Monitor", layout="wide")

COIN_1 = "tia"
COIN_2 = "alch"
VS_CURRENCY = "usd"
REFRESH_EVERY = 60  # sekundy

# === API Key CoinMarketCap ===
API_KEY = "53eb73e4-dd42-4a96-9f82-de13bda828bc"
HEADERS = {"X-CMC_PRO_API_KEY": API_KEY}

# === Funkcje pomocnicze ===
@st.cache_data(ttl=REFRESH_EVERY)
def fetch_prices():
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    symbols = f"{COIN_1},{COIN_2}"
    params = {"symbol": symbols.upper(), "convert": VS_CURRENCY.upper()}
    response = requests.get(url, headers=HEADERS, params=params)
    data = response.json()
    tia_price = data["data"][COIN_1.upper()]["quote"][VS_CURRENCY.upper()]["price"]
    alch_price = data["data"][COIN_2.upper()]["quote"][VS_CURRENCY.upper()]["price"]
    return tia_price, alch_price


def calculate_indicators(price_series):
    df = pd.Series(price_series).to_frame("price")
    df["EMA20"] = df["price"].ewm(span=20).mean()
    df["EMA50"] = df["price"].ewm(span=50).mean()
    df["RSI"] = compute_rsi(df["price"])
    return df


def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def generate_strategy(ratio):
    if ratio > 1.15:
        return "➡️ Zamień 25% TIA na ALCH - możliwe wykupienie TIA"
    elif ratio < 0.85:
        return "⬅️ Zamień 25% ALCH na TIA - możliwe wyprzedanie TIA"
    else:
        return "🤝 Trzymaj - brak wyraźnego sygnału"


# === Layout ===
st.title("📈 TIA/ALCH Monitor - Live v2")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Cena TIA")
    tia_price, alch_price = fetch_prices()
    st.metric("TIA", f"${tia_price:.4f}")

with col2:
    st.markdown("### Cena ALCH")
    st.metric("ALCH", f"${alch_price:.4f}")

with col3:
    ratio = tia_price / alch_price
    st.markdown("### Stosunek TIA / ALCH")
    st.metric("TIA/ALCH", f"{ratio:.4f}")

st.divider()

# Wykres
prices_df = pd.DataFrame({"TIA": [tia_price], "ALCH": [alch_price], "timestamp": [datetime.now()]})
st.markdown("#### Wykres TIA/ALCH (1 punkt)")
fig = go.Figure()
fig.add_trace(go.Scatter(x=prices_df["timestamp"], y=prices_df["TIA"] / prices_df["ALCH"],
                         mode="markers+lines", name="TIA/ALCH"))
fig.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=0))
st.plotly_chart(fig, use_container_width=True)

# Strategia
st.divider()
st.markdown("### 🔍 Sygnał Strategiczny")
strategy = generate_strategy(ratio)
st.info(strategy)

st.caption(f"Ostatnia aktualizacja: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
