
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
from datetime import datetime

if "tia" not in st.session_state:
    st.session_state.tia = 3151.87
if "alch" not in st.session_state:
    st.session_state.alch = 15117.82

API_KEY = "53eb73e4-dd42-4a96-9f82-de13bda828bc"
CMC_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
HEADERS = {"X-CMC_PRO_API_KEY": API_KEY}

@st.cache_data(ttl=300)
def fetch_prices():
    params = {"symbol": "TIA,ALCH", "convert": "USD"}
    r = requests.get(CMC_URL, headers=HEADERS, params=params)
    data = r.json()
    tia = data["data"]["TIA"]["quote"]["USD"]["price"]
    alch = data["data"]["ALCH"]["quote"]["USD"]["price"]
    return tia, alch

st.set_page_config(page_title="TIA/ALCH Cloud Manual", layout="wide")
st.title("📊 TIA/ALCH – Chmurowa Wersja z Ręcznym Portfelem")

tia_price, alch_price = fetch_prices()
ratio = tia_price / alch_price

# Symulowana historia
ratios = [ratio + (i - 10) * 0.1 for i in range(21)]
timestamps = pd.date_range(end=datetime.now(), periods=21, freq="H")
df = pd.DataFrame({"timestamp": timestamps, "ratio": ratios})

mean = df["ratio"].mean()
std = df["ratio"].std()
upper = mean + std
lower = mean - std

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df["timestamp"], df["ratio"], label="TIA/ALCH", color="orange")
ax.axhline(mean, color="gray", linestyle="--", label="Średnia")
ax.axhline(upper, color="red", linestyle="--", label="+1σ (Kup ALCH)")
ax.axhline(lower, color="green", linestyle="--", label="-1σ (Kup TIA)")
ax.plot(timestamps[-1], ratio, "o", color="blue", label="Obecnie")
ax.set_title("TIA/ALCH – CoinMarketCap")
ax.legend()
ax.grid(True)
st.pyplot(fig)

st.markdown("### 💼 Portfel")
st.write(f"TIA: {st.session_state.tia:.2f}")
st.write(f"ALCH: {st.session_state.alch:.2f}")

# Ręczna edycja portfela
with st.expander("🛠️ Edytuj portfel ręcznie"):
    new_tia = st.number_input("Nowa wartość TIA", value=st.session_state.tia, format="%.2f")
    new_alch = st.number_input("Nowa wartość ALCH", value=st.session_state.alch, format="%.2f")
    if st.button("Zapisz zmiany portfela"):
        st.session_state.tia = new_tia
        st.session_state.alch = new_alch
        st.success("Zaktualizowano portfel.")
        st.rerun()

# Ręczny formularz przed/po
with st.form("manual_swap_form"):
    st.markdown("### ✍️ Ręczne wpisanie wymiany")
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

# Sygnał
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

st.caption(f"Źródło: CoinMarketCap • Stosunek: {ratio:.2f} • TIA: ${tia_price:.4f} • ALCH: ${alch_price:.4f}")
