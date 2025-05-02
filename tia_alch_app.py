
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from datetime import datetime

# Portfel
wallet = {
    "TIA": 4202.48 - 1050.61,
    "ALCH": 15117.82
}

# CoinMarketCap API
API_KEY = "53eb73e4-dd42-4a96-9f82-de13bda828bc"
HEADERS = {"X-CMC_PRO_API_KEY": API_KEY}
CMC_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

# Funkcja pobierająca cenę
@st.cache_data(ttl=300)
def fetch_prices():
    symbols = "TIA,ALCH"
    params = {"symbol": symbols, "convert": "USD"}
    response = requests.get(CMC_URL, headers=HEADERS, params=params)
    data = response.json()
    tia = data["data"]["TIA"]["quote"]["USD"]["price"]
    alch = data["data"]["ALCH"]["quote"]["USD"]["price"]
    return tia, alch

st.set_page_config(page_title="TIA/ALCH Cloud", layout="wide")
st.title("📊 TIA/ALCH – Strategiczna aplikacja chmurowa (CoinMarketCap)")

# Pobierz dane
tia_price, alch_price = fetch_prices()
ratio = tia_price / alch_price

# Symulowana historia do wykresu
ratios = [ratio + (i - 10) * 0.1 for i in range(21)]
timestamps = pd.date_range(end=datetime.now(), periods=21, freq="H")
df = pd.DataFrame({"timestamp": timestamps, "ratio": ratios})

mean = df["ratio"].mean()
std = df["ratio"].std()
upper = mean + std
lower = mean - std

# Obecny sygnał
if ratio > upper:
    signal = "🔴 Zamień część TIA na ALCH"
elif ratio < lower:
    signal = "🟢 Zamień część ALCH na TIA"
else:
    signal = "🟡 Trzymaj"

# Wykres
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df["timestamp"], df["ratio"], label="TIA/ALCH", color="orange")
ax.axhline(mean, linestyle="--", color="gray", label="Średnia")
ax.axhline(upper, linestyle="--", color="red", label="+1σ")
ax.axhline(lower, linestyle="--", color="green", label="-1σ")
ax.plot(datetime.now(), ratio, "o", color="blue", label="Obecnie")
ax.set_title("Stosunek TIA/ALCH (CMC, dane 1h symulowane)")
ax.legend()
ax.grid(True)
st.pyplot(fig)

# Portfel
st.markdown("### 💼 Stan portfela")
st.write(f"**TIA:** {wallet['TIA']:.2f}")
st.write(f"**ALCH:** {wallet['ALCH']:.2f}")

# Sygnał
st.markdown("### 📌 Obecny sygnał")
st.success(signal)

# Propozycja konwersji
if "ALCH" in signal and wallet["ALCH"] > 0:
    alch_to_swap = wallet["ALCH"] * 0.25
    tia_recv = alch_to_swap / ratio
    st.info(f"Zamień {alch_to_swap:.2f} ALCH na ~{tia_recv:.2f} TIA")
elif "TIA" in signal and wallet["TIA"] > 0:
    tia_to_swap = wallet["TIA"] * 0.25
    alch_recv = tia_to_swap * ratio
    st.info(f"Zamień {tia_to_swap:.2f} TIA na ~{alch_recv:.2f} ALCH")
else:
    st.info("Brak zalecanej akcji – obserwuj rynek.")

st.caption(f"Źródło: CoinMarketCap | Stosunek: {ratio:.2f} | TIA: ${tia_price:.4f} | ALCH: ${alch_price:.4f}")
