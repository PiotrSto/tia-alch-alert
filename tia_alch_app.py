
import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials
import os

st.set_page_config(page_title="TIA/ALCH – Cloud z Google Sheets", layout="wide")
st.title("📊 TIA/ALCH Tracker – Cloud z Google Sheets")

# Autoryzacja do Google Sheets z secretów
GOOGLE_SERVICE_ACCOUNT = os.environ.get("GOOGLE_SERVICE_ACCOUNT")
if not GOOGLE_SERVICE_ACCOUNT:
    st.error("❌ Nie znaleziono sekretu GOOGLE_SERVICE_ACCOUNT.")
    st.stop()

creds = Credentials.from_service_account_info(json.loads(GOOGLE_SERVICE_ACCOUNT))
client = gspread.authorize(creds)

# Ładowanie danych z arkusza
spreadsheet = client.open("TIA_ALCH_Portfel")
sheet = spreadsheet.worksheet("portfel")
data = sheet.get_all_values()
df = pd.DataFrame(data[1:], columns=data[0])

# Wyświetlenie danych
st.subheader("📦 Portfel")
st.dataframe(df)
