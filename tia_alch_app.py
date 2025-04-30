# TIA/ALCH Streamlit App (v3) - z Telegramem, wskaźnikami i historią

import streamlit as st
import pandas as pd
import requests
import time
import plotly.graph_objs as go
from datetime import datetime
import os

# Telegram config
BOT_TOKEN = "7696807946:AAFyq_gGVq3yNYI8uM_CBjXhkMrI4Umfw-0"
CHAT_ID = "1508106512"

# Ustawienia
st.set_page_config(page_title="TIA/ALCH Monitor", layout="wide")
COIN_1 = "tia"
COIN_2 = "alch"
VS_CURRENCY = "usd"
REFRESH_EVERY = 60

API_KEY = "53eb73e4-dd42-4a96-9f82-de13bda828bc"
HEADERS = {"X-CMC_PRO_API_KEY": API_KEY}

# Funkcje
@st.cache_data(ttl=REFRESH_EVERY)
def fetch_prices():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    symbols = f"{COIN_1},{COIN_2}"
    params = {"symbol": symbols.upper(), "convert": VS_CURRENCY.upper()}
    response = requests.get(url, headers=HEADERS, params=params)
    data = response.json()
    tia = data["data"][COIN_1.upper()]["quote"][VS_CURRENCY.upper()]["price"]
    alch = data["data"][COIN_2.upper()]["quote"][VS_CURRENCY.upper()]["price"]
    return tia, alch

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_indicators(prices):
    df = pd.Series(prices).to_frame("price")
    df["EMA20"] = df["price"].ewm(span=20).mean()
    df["EMA50"] = df["price"].ewm(span=50).mean()
    df["EMA200"] = df["price"].ewm(span=200).mean()
    df["RSI"] = compute_rsi(df["price"])
    return df

def generate_signal(ratio):
    if ratio > 1.15:
        return "🔴 Zamień 25% TIA na ALCH"
    elif ratio < 0.85:
        return "🟢 Zamień 25% ALCH na TIA"
    else:
        return "🟡 Trzymaj pozycję"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=payload)

# Ceny
tia_price, alch_price = fetch_prices()
ratio = tia_price / alch_price
signal = generate_signal(ratio)

# Historia
history_file = "history.csv"
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
new_row = pd.DataFrame([[now, tia_price, alch_price, ratio, signal]], 
    columns=["timestamp", "tia", "alch", "ratio", "signal"])
if os.path.exists(history_file):
    df_old = pd.read_csv(history_file)
    df_new = pd.concat([df_old, new_row], ignore_index=True)
    df_new.to_csv(history_file, index=False)
else:
    new_row.to_csv(history_file, index=False)

# Telegram
if signal != "🟡 Trzymaj pozycję":
    msg = f"{signal}\nTIA: ${tia_price:.4f}\nALCH: ${alch_price:.4f}\nStosunek: {ratio:.4f}"
    send_telegram_message(msg)

# Interfejs
st.title("📈 TIA/ALCH Monitor v3")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Cena TIA", f"${tia_price:.4f}")
with col2:
    st.metric("Cena ALCH", f"${alch_price:.4f}")
with col3:
    st.metric("Stosunek TIA/ALCH", f"{ratio:.4f}")

st.subheader("🔍 Sygnał Strategiczny")
st.success(signal)

# Wykres
st.subheader("📊 Wykres Stosunku")
df_chart = pd.read_csv(history_file)
fig = go.Figure()
fig.add_trace(go.Scatter(x=df_chart["timestamp"], y=df_chart["ratio"], mode="lines+markers", name="TIA/ALCH"))
st.plotly_chart(fig, use_container_width=True)

# Historia
st.subheader("🗂 Historia Strategii")
st.dataframe(df_chart.tail(10), use_container_width=True)
