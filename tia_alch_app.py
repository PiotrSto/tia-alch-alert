
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objs as go
from datetime import datetime
import os

# Stan portfela
wallet = {"TIA": 4202.48, "ALCH": 0}

# API CoinMarketCap
API_KEY = "53eb73e4-dd42-4a96-9f82-de13bda828bc"
HEADERS = {"X-CMC_PRO_API_KEY": API_KEY}
REFRESH_EVERY = 60
history_file = "history.csv"

st.set_page_config(page_title="TIA/ALCH Tracker", layout="wide")

@st.cache_data(ttl=REFRESH_EVERY)
def fetch_prices():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    params = {"symbol": "TIA,ALCH", "convert": "USD"}
    r = requests.get(url, headers=HEADERS, params=params)
    data = r.json()
    tia = data["data"]["TIA"]["quote"]["USD"]["price"]
    alch = data["data"]["ALCH"]["quote"]["USD"]["price"]
    return tia, alch

# Sygnał na podstawie aktualnego stanu portfela
def generate_signal(ratio):
    if ratio > 1.15 and wallet["TIA"] > 0:
        return "🔴 Zamień część TIA na ALCH"
    else:
        return "🟡 Trzymaj"

# Pobranie danych
tia_price, alch_price = fetch_prices()
ratio = tia_price / alch_price
signal = generate_signal(ratio)
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
row = pd.DataFrame([[now, tia_price, alch_price, ratio, signal]],
                   columns=["timestamp", "tia", "alch", "ratio", "signal"])

# Historia
if os.path.exists(history_file):
    old = pd.read_csv(history_file)
    combined = pd.concat([old, row], ignore_index=True)
else:
    combined = row
combined.to_csv(history_file, index=False)

# UI
st.title("📊 TIA/ALCH Tracker – wersja z portfelem")

col1, col2, col3 = st.columns(3)
col1.metric("Cena TIA", f"${tia_price:.4f}")
col2.metric("Cena ALCH", f"${alch_price:.4f}")
col3.metric("Stosunek TIA/ALCH", f"{ratio:.4f}")

st.markdown("### Stan portfela")
st.write(f'**TIA**: {wallet["TIA"]} | **ALCH**: {wallet["ALCH"]}')

# Szacowana wartość wymiany (jeśli sygnał aktywny)
if "Zamień" in signal:
    tia_do_sprzedania = wallet["TIA"] * 0.25
    alch_do_otrzymania = tia_do_sprzedania * ratio
    st.info(f"Rekomendacja: wymień **{tia_do_sprzedania:.2f} TIA** na **{alch_do_otrzymania:.2f} ALCH**")

st.markdown("### Sygnał")
st.success(signal)

# Wykres
df_chart = combined.copy()
df_chart["timestamp"] = pd.to_datetime(df_chart["timestamp"])
fig = go.Figure()
fig.add_trace(go.Scatter(x=df_chart["timestamp"], y=df_chart["ratio"],
                         mode="lines+markers", name="TIA/ALCH"))

# Kolorowe punkty
for i, row in df_chart.iterrows():
    color = "yellow"
    if "TIA" in row["signal"]:
        color = "red"
    fig.add_trace(go.Scatter(
        x=[row["timestamp"]], y=[row["ratio"]],
        mode="markers", marker=dict(color=color, size=10),
        showlegend=False
    ))

fig.update_layout(height=400, margin=dict(t=30))
st.plotly_chart(fig, use_container_width=True)

st.markdown("### Historia")
st.dataframe(df_chart.tail(10), use_container_width=True)
