
import streamlit as st
import requests
import matplotlib.pyplot as plt

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
def get_price(symbol):
    url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    params = {"symbol": symbol, "convert": "USD"}
    r = requests.get(url, headers=HEADERS, params=params)
    data = r.json()
    return data["data"][symbol]["quote"]["USD"]["price"]

st.set_page_config(page_title="TIA/ALCH – Wizualny Alert", layout="wide")
st.title("📊 TIA/ALCH – Wizualny alert z CoinMarketCap")

try:
    tia = get_price("TIA")
    alch = get_price("ALCH")
    ratio = tia / alch

    st.metric("Cena TIA (USD)", f"${tia:.4f}")
    st.metric("Cena ALCH (USD)", f"${alch:.4f}")
    st.metric("Stosunek TIA / ALCH", f"{ratio:.2f}")

    # Progi decyzyjne
    upper = 17.0
    lower = 15.5

    if ratio > upper:
        signal = "🔴 Kup ALCH za TIA"
        color = "red"
    elif ratio < lower:
        signal = "🟢 Kup TIA za ALCH"
        color = "green"
    else:
        signal = "🟡 Trzymaj"
        color = "orange"

    st.subheader(f"Sygnał: {signal}")

    try:
        with open(STATE_FILE, "r") as f:
            last_signal = f.read().strip()
    except:
        last_signal = ""
    if signal != last_signal:
        send_telegram_alert(f"[ALERT TIA/ALCH]\nSygnał: {signal}\nStosunek: {ratio:.2f}")
        with open(STATE_FILE, "w") as f:
            f.write(signal)

    # WIZUALIZACJA POZIOMÓW
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.set_xlim(14.5, 18.5)
    ax.axvspan(14.5, lower, color="green", alpha=0.2, label="Kup TIA za ALCH")
    ax.axvspan(lower, upper, color="orange", alpha=0.2, label="Trzymaj")
    ax.axvspan(upper, 18.5, color="red", alpha=0.2, label="Kup ALCH za TIA")
    ax.axvline(ratio, color=color, linewidth=3, label=f"Aktualny: {ratio:.2f}")
    ax.set_title("📍 Pozycja TIA/ALCH względem progów decyzyjnych")
    ax.set_xlabel("Stosunek TIA / ALCH")
    ax.get_yaxis().set_visible(False)
    ax.legend()
    st.pyplot(fig)

    st.caption("Dane z CoinMarketCap, odświeżane co 10 minut – z wizualizacją")
except:
    st.error("Błąd pobierania danych z CoinMarketCap")
