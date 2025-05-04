
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from datetime import datetime

if "tia" not in st.session_state:
    st.session_state.tia = 3151.87
if "alch" not in st.session_state:
    st.session_state.alch = 15117.82

KUCOIN_URL = "https://api.kucoin.com/api/v1/market/candles"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_kucoin_data(symbol: str, interval: str = "1hour", limit: int = 168):
    params = {
        "type": interval,
        "symbol": symbol
    }
    try:
        r = requests.get(KUCOIN_URL, headers=HEADERS, params=params)
        r.raise_for_status()
        raw = r.json()["data"]
        df = pd.DataFrame(raw, columns=[
            "timestamp", "open", "close", "high", "low", "volume", "turnover"
        ])
        df["timestamp"] = pd.to_datetime(df["timestamp"].astype(float), unit="s")
        df["close"] = df["close"].astype(float)
        return df[["timestamp", "close"]].sort_values("timestamp").tail(limit)
    except Exception as e:
        st.error(f"❌ Błąd pobierania danych z KuCoin: {e}")
        return pd.DataFrame(columns=["timestamp", "close"])

st.set_page_config(page_title="TIA/ALCH Cloud KuCoin", layout="wide")
st.title("📊 TIA/ALCH – Wersja Chmurowa z Historią z KuCoin")

tia_df = fetch_kucoin_data("TIA-USDT")
alch_df = fetch_kucoin_data("ALCH-USDT")

if tia_df.empty or alch_df.empty:
    st.error("Brak danych z KuCoin.")
    st.stop()

df = pd.merge(tia_df, alch_df, on="timestamp", suffixes=("_TIA", "_ALCH"))
df["ratio"] = df["close_TIA"] / df["close_ALCH"]
df = df.sort_values("timestamp")

mean = df["ratio"].mean()
std = df["ratio"].std()
upper = mean + std
lower = mean - std

last = df.iloc[-1]
ratio = last["ratio"]
now = last["timestamp"]

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df["timestamp"], df["ratio"], label="TIA/ALCH", color="orange")
ax.axhline(mean, color="gray", linestyle="--", label="Średnia")
ax.axhline(upper, color="red", linestyle="--", label="+1σ (Kup ALCH)")
ax.axhline(lower, color="green", linestyle="--", label="-1σ (Kup TIA)")
ax.plot(now, ratio, "o", color="blue", label="Obecnie")
ax.set_title("Stosunek TIA/ALCH – dane KuCoin (1h)")
ax.legend()
ax.grid(True)
st.pyplot(fig)

st.markdown("### 💼 Portfel (obecny stan)")
st.write(f"TIA: {st.session_state.tia:.2f}")
st.write(f"ALCH: {st.session_state.alch:.2f}")

st.markdown("### ✏️ Edytuj portfel")
with st.form("edit_wallet_form"):
    new_tia = st.number_input("TIA:", value=st.session_state.tia, format="%.2f")
    new_alch = st.number_input("ALCH:", value=st.session_state.alch, format="%.2f")
    if st.form_submit_button("Zapisz nowy portfel"):
        st.session_state.tia = new_tia
        st.session_state.alch = new_alch
        st.success("Zaktualizowano portfel.")
        st.rerun()

st.markdown("### ✍️ Ręczne wpisanie wymiany")
with st.form("manual_swap_form"):
    direction = st.radio("Rodzaj zamiany", ["TIA → ALCH", "ALCH → TIA"])
    give_amount = st.number_input("Ilość przed wymianą", min_value=0.0, format="%.2f")
    receive_amount = st.number_input("Ilość po wymianie", min_value=0.0, format="%.2f")
    submit = st.form_submit_button("Zapisz wymianę")

    if submit and give_amount > 0 and receive_amount > 0:
        if direction == "TIA → ALCH" and give_amount <= st.session_state.tia:
            st.session_state.tia -= give_amount
            st.session_state.alch += receive_amount
            st.success(f"Zapisano: {give_amount:.2f} TIA → {receive_amount:.2f} ALCH")
            st.rerun()
        elif direction == "ALCH → TIA" and give_amount <= st.session_state.alch:
            st.session_state.alch -= give_amount
            st.session_state.tia += receive_amount
            st.success(f"Zapisano: {give_amount:.2f} ALCH → {receive_amount:.2f} TIA")
            st.rerun()
        else:
            st.error("Za mało środków na tę operację.")

st.markdown("### 📌 Sygnał")
if ratio > upper and st.session_state.tia > 0:
    swap = st.session_state.tia * 0.25
    receive = swap * ratio
    st.success(f"🔴 Zamień 25% TIA ({swap:.2f}) → {receive:.2f} ALCH")
elif ratio < lower and st.session_state.alch > 0:
    swap = st.session_state.alch * 0.25
    receive = swap / ratio
    st.success(f"🟢 Zamień 25% ALCH ({swap:.2f}) → {receive:.2f} TIA")
else:
    st.info("🟡 Trzymaj – brak zalecanej akcji.")

st.caption(f"Dane z KuCoin • Stosunek: {ratio:.2f} • Aktualizacja: {now.strftime('%Y-%m-%d %H:%M')}")
