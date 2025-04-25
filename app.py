
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="TIA/ALCH Alert", layout="wide")

# Funkcja do pobierania danych z CoinGecko
def fetch_price_data(coin_id, vs_currency="eur", days=7, interval="hourly"):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": vs_currency,
        "days": days,
        "interval": interval
    }
    response = requests.get(url, params=params)
    data = response.json()
    prices = data["prices"]
    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df

# Pobieranie danych
df_tia = fetch_price_data("celestia")
df_alch = fetch_price_data("alchemy-pay")

# Łączenie danych
df = pd.merge(df_tia, df_alch, on="timestamp", suffixes=("_tia", "_alch"))
df["ratio"] = df["price_tia"] / df["price_alch"]

# Obliczanie średniej i odchyleń
mean_ratio = df["ratio"].mean()
std_ratio = df["ratio"].std()
upper_bound = mean_ratio + std_ratio
lower_bound = mean_ratio - std_ratio
latest_ratio = df["ratio"].iloc[-1]

# Określanie sygnału
if latest_ratio > upper_bound:
    signal = "🔴 Kup ALCH za TIA"
elif latest_ratio < lower_bound:
    signal = "🟢 Kup TIA za ALCH"
else:
    signal = "🟡 Trzymaj"

# Wyświetlanie wyników
st.title("📊 TIA/ALCH Alert (EUR)")
st.markdown(f"### Sygnał: {signal}")
st.markdown(f"**Aktualny stosunek:** {latest_ratio:.2f}")
st.markdown(f"**Średni stosunek:** {mean_ratio:.2f}")
st.markdown(f"**Odchylenie standardowe:** {std_ratio:.2f}")

# Wykres
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df["timestamp"], df["ratio"], label="Stosunek TIA/ALCH")
ax.axhline(mean_ratio, color="gray", linestyle="--", label="Średnia")
ax.axhline(upper_bound, color="red", linestyle="--", label="Górna granica")
ax.axhline(lower_bound, color="green", linestyle="--", label="Dolna granica")
ax.set_xlabel("Data")
ax.set_ylabel("Stosunek")
ax.legend()
st.pyplot(fig)
