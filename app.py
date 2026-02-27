import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
from PIL import Image

st.set_page_config(page_title="Zpracování faktur", layout="wide")
st.title("📸 Chytré párování faktur s AI")

try:
  genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
  st.error("Chybí API klíč! Zkontroluj nastavení Secrets ve Streamlitu.")
  st.stop()

st.subheader("1. Nahraj svůj číselník (Excel)")
excel_file = st.file_uploader("Vyber soubor .xlsx (Sloupec A = z faktury, Sloupec B = tvůj kód)", type=["xlsx"])

df_ciselnik = None
if excel_file:
  df_ciselnik = pd.read_excel(excel_file)
st.success("Číselník načten! Můžeš fotit.")

st.divider()

st.subheader("2. Vyfoť nebo nahraj fakturu")
tab1, tab2 = st.tabs(["📷 Vyfotit mobilem", "📁 Nahrát z PC"])

foto = None
with tab1:
  foto_cam = st.camera_input("Vyfoť fakturu zde")
if foto_cam: foto = foto_cam
with tab2:
  foto_up = st.file_uploader("Nebo nahraj fotku", type=["png", "jpg", "jpeg"])
if foto_up: foto = foto_up

if foto:
st.image(foto, caption="Tuhle fakturu jdeme číst", width=400)
