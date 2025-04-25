
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

@st.cache_data(ttl=600)
def fetch_prices(token_id):
    url = f"https://api.coingecko.com/api/v3/coins/{token_id}/market_chart?vs_currency=usd&days=7&interval=hourly"
    response = requests.get(url)
    data = response.json()
    return pd.DataFrame(data['prices'], columns=['timestamp', 'price'])

st.set_page_config(page_title="TIA/ALCH – CoinGecko App", layout="wide")
st.title("📈 TIA/ALCH – Wykres i alerty z CoinGecko (24/7 Telegram)")

try:
    tia_df = fetch_prices("celestia")
    alch_df = fetch_prices("alchemist-ai")

    for df in [tia_df, alch_df]:
        df['Data'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.drop(columns='timestamp', inplace=True)

    df = pd.merge(tia_df, alch_df, on="Data", suffixes=("_TIA", "_ALCH"))
    df["Stosunek"] = df["price_TIA"] / df["price_ALCH"]

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

    zmiana = (df["Stosunek"].iloc[-1] - df["Stosunek"].iloc[-12]) / df["Stosunek"].iloc[-12] * 100
    if zmiana > 2:
        momentum_signal = "⚡ Szybki wzrost – rozważ sprzedaż ALCH"
    elif zmiana < -2:
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
    ax.set_title("Stosunek TIA/ALCH – CoinGecko (1h)")
    ax.legend()
    st.pyplot(fig)

    st.subheader(f"Sygnał: {signal}")
    st.caption(momentum_signal)
    st.caption("Dane z CoinGecko, odświeżane co 10 minut")
except:
    st.error("Błąd w pobieraniu danych z CoinGecko. Spróbuj później.")
