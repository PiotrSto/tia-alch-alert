
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

st.set_page_config(page_title="TIA/ALCH – GATEIO", layout="wide")

if "tia" not in st.session_state:
    st.session_state.tia = 3151.87
if "alch" not in st.session_state:
    st.session_state.alch = 15117.82

def fetch_price_df(symbol_url):
    try:
        r = requests.get(symbol_url)
        r.raise_for_status()
        data = r.json()
        k = data.get("data") or data.get("result") or data.get("candles") or list(data.values())[0]
        df = pd.DataFrame(k)
        df["timestamp"] = pd.to_datetime(df.iloc[:, 0].astype(float), unit="s")
        df["close"] = df.iloc[:, 1].astype(float)
        return df[["timestamp", "close"]].sort_values("timestamp").tail(168)
    except Exception as e:
        st.error(f"Błąd pobierania danych z GATEIO: {e}")
        return pd.DataFrame(columns=["timestamp", "close"])

st.title("📊 TIA/ALCH – GATEIO")

tia_url = "https://api.gateio.ws/api/v4/spot/candlesticks?currency_pair=TIA_USDT&interval=1h&limit=168"
alch_url = "https://api.gateio.ws/api/v4/spot/candlesticks?currency_pair=ALCH_USDT&interval=1h&limit=168"

tia_df = fetch_price_df(tia_url)
alch_df = fetch_price_df(alch_url)

if tia_df.empty or alch_df.empty:
    st.error("Brak danych historycznych.")
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
ax.axhline(upper, color="red", linestyle="--", label="+1σ (kup ALCH)")
ax.axhline(lower, color="green", linestyle="--", label="-1σ (kup TIA)")
ax.plot(now, ratio, "o", color="blue", label="Obecnie")
ax.legend()
st.pyplot(fig)

st.subheader("💼 Portfel")
st.write(f"TIA: {st.session_state.tia:.2f}")
st.write(f"ALCH: {st.session_state.alch:.2f}")

with st.form("edit_wallet_form"):
    new_tia = st.number_input("TIA:", value=st.session_state.tia, format="%.2f")
    new_alch = st.number_input("ALCH:", value=st.session_state.alch, format="%.2f")
    if st.form_submit_button("Zapisz nowy portfel"):
        st.session_state.tia = new_tia
        st.session_state.alch = new_alch
        st.success("Zaktualizowano portfel.")
        st.rerun()

st.subheader("✍️ Wpisz ręcznie wymianę")
with st.form("manual_swap_form"):
    direction = st.radio("Rodzaj zamiany", ["TIA → ALCH", "ALCH → TIA"])
    give = st.number_input("Ilość przed wymianą", min_value=0.0, format="%.2f")
    receive = st.number_input("Ilość po wymianie", min_value=0.0, format="%.2f")
    if st.form_submit_button("Zapisz wymianę") and give > 0 and receive > 0:
        if direction == "TIA → ALCH" and give <= st.session_state.tia:
            st.session_state.tia -= give
            st.session_state.alch += receive
            st.success(f"Zamieniono: {give:.2f} TIA → {receive:.2f} ALCH")
            st.rerun()
        elif direction == "ALCH → TIA" and give <= st.session_state.alch:
            st.session_state.alch -= give
            st.session_state.tia += receive
            st.success(f"Zamieniono: {give:.2f} ALCH → {receive:.2f} TIA")
            st.rerun()
        else:
            st.error("Za mało środków na tę wymianę.")

st.subheader("📌 Sygnał")
if ratio > upper and st.session_state.tia > 0:
    amt = st.session_state.tia * 0.25
    out = amt * ratio
    st.success(f"🔴 Zamień 25% TIA ({amt:.2f}) → {out:.2f} ALCH")
elif ratio < lower and st.session_state.alch > 0:
    amt = st.session_state.alch * 0.25
    out = amt / ratio
    st.success(f"🟢 Zamień 25% ALCH ({amt:.2f}) → {out:.2f} TIA")
else:
    st.info("🟡 Brak akcji – trzymaj pozycję.")
