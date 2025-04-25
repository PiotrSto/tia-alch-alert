
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import numpy as np
from datetime import datetime

TELEGRAM_TOKEN = "7696807946:AAFyq_gGVq3yNYI8uM_CBjXhkMrI4Umfw-0"
CHAT_ID = "1508106512"
STATE_FILE = "last_signal.txt"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except:
        pass

def fetch_kline(symbol, interval="60", limit=168):
    url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    raw = data["result"]["list"]
    df = pd.DataFrame(raw, columns=[
        "timestamp", "open", "high", "low", "close", "volume", "turnover"
    ])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    return df[["timestamp", "close"]].rename(columns={"timestamp": "Data", "close": f"{symbol}_close"})

st.set_page_config(page_title="TIA/ALCH – Alert System", layout="wide")
st.title("📈 TIA/ALCH – Live Alert System 24/7 (ByBit + Telegram)")

tia_df = fetch_kline("TIAUSDT")
alch_df = fetch_kline("ALCHUSDT")

if tia_df.empty or alch_df.empty:
    st.error("Brak danych z ByBit.")
else:
    df = pd.merge(tia_df, alch_df, on="Data")
    df["Stosunek"] = df["TIAUSDT_close"] / df["ALCHUSDT_close"]

    srednia = df["Stosunek"].mean()
    std = df["Stosunek"].std()
    gorna = srednia + std
    dolna = srednia - std
    ostatni = df.iloc[-1]["Stosunek"]

    if ostatni > gorna:
        signal = "🔴 Kup ALCH za TIA"
    elif ostatni < dolna:
        signal = "🟢 Kup TIA za ALCH"
    else:
        signal = "🟡 Trzymaj"

    momentum_df = df.tail(12)
    zmiana_12h = (momentum_df["Stosunek"].iloc[-1] - momentum_df["Stosunek"].iloc[0]) / momentum_df["Stosunek"].iloc[0] * 100
    if zmiana_12h > 2:
        momentum_signal = "⚡ Szybki wzrost – rozważ sprzedaż ALCH"
    elif zmiana_12h < -2:
        momentum_signal = "⚡ Szybki spadek – rozważ sprzedaż TIA"
    else:
        momentum_signal = "⚡ Bez silnego trendu"

    try:
        with open(STATE_FILE, "r") as f:
            last_signal = f.read().strip()
    except:
        last_signal = ""
    if signal != last_signal:
        send_telegram_alert(f"[ALERT TIA/ALCH]\nSygnał: {signal}\nStosunek: {ostatni:.2f}")
        with open(STATE_FILE, "w") as f:
            f.write(signal)

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(df["Data"], df["Stosunek"], label="Stosunek TIA/ALCH", color="orange")
    ax.axhline(srednia, color="gray", linestyle="--", label="Średnia")
    ax.axhline(gorna, color="red", linestyle="--", label="Kup ALCH")
    ax.axhline(dolna, color="green", linestyle="--", label="Kup TIA")
    ax.set_title("Stosunek TIA/ALCH – ByBit (1h)")
    ax.legend()
    st.pyplot(fig)

    st.subheader(f"Sygnał: {signal}")
    st.caption(momentum_signal)
