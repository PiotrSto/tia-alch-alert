
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta
import time

TELEGRAM_TOKEN = "7696807946:AAFyq_gGVq3yNYI8uM_CBjXhkMrI4Umfw-0"
CHAT_ID = "1508106512"
CMC_API_KEY = "53eb73e4-dd42-4a96-9f82-de13bda828bc"
STATE_FILE = "last_signal.txt"

HEADERS = {
    "Accepts": "application/json",
    "X-CMC_PRO_API_KEY": CMC_API_KEY,
}

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except:
        pass

@st.cache_data(ttl=600)
def fetch_cmc_price_history(symbol):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/historical"
    end_time = int(time.time())
    start_time = end_time - 7 * 24 * 60 * 60  # 7 dni wstecz
    params = {
        "symbol": symbol,
        "time_start": start_time,
        "time_end": end_time,
        "interval": "hourly",
        "convert": "USD"
    }
    r = requests.get(url, headers=HEADERS, params=params)
    data = r.json()
    prices = data["data"]["quotes"]
    df = pd.DataFrame([(q["timestamp"], q["quote"]["USD"]["price"]) for q in prices], columns=["Data", f"{symbol}_price"])
    df["Data"] = pd.to_datetime(df["Data"])
    return df

st.set_page_config(page_title="TIA/ALCH – CoinMarketCap App", layout="wide")
st.title("📈 TIA/ALCH – Dane z CoinMarketCap + alerty Telegram 24/7")

try:
    tia_df = fetch_cmc_price_history("TIA")
    alch_df = fetch_cmc_price_history("ALCH")

    df = pd.merge(tia_df, alch_df, on="Data")
    df["Stosunek"] = df["TIA_price"] / df["ALCH_price"]

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
    ax.set_title("Stosunek TIA/ALCH – CoinMarketCap (1h)")
    ax.legend()
    st.pyplot(fig)

    st.subheader(f"Sygnał: {signal}")
    st.caption(momentum_signal)
    st.caption("Dane z CoinMarketCap, odświeżane co 10 minut")
except:
    st.error("Błąd w pobieraniu danych z CoinMarketCap. Sprawdź połączenie lub API.")
