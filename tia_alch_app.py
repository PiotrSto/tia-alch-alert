import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

st.set_page_config(page_title="TIA/ALCH Tracker CMC", layout="wide")
st.title("📊 TIA/ALCH – Live Tracker (USD, CMC)")

@st.cache_data(ttl=300)
def fetch_price_cmc(symbol: str):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": "YOUR_CMC_API_KEY"}
    params = {"symbol": symbol, "convert": "USD"}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    return data["data"][symbol]["quote"]["USD"]["price"]

tia_price = fetch_price_cmc("TIA")
alch_price = fetch_price_cmc("ALCH")

ratio = tia_price / alch_price
mean = 16.5
std = 0.8
upper = mean + std
lower = mean - std

if ratio > upper:
    signal = "🔴 Kup ALCH za TIA"
elif ratio < lower:
    signal = "🟢 Kup TIA za ALCH"
else:
    signal = "🟡 Trzymaj"

st.metric("Obecny stosunek TIA/ALCH", f"{ratio:.2f}", help=signal)