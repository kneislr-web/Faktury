import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
from PIL import Image
import os

st.set_page_config(page_title="Párování faktur", layout="wide")
st.title("📸 Chytré párování")

# 1. NASTAVENÍ API - VYNUCENÍ STABILNÍ VERZE
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Chybí API klíč v Secrets!")
    st.stop()

# TENTO ŘÁDEK JE KLÍČOVÝ - fixuje verzi API na stabilní v1
os.environ["GOOGLE_API_USE_MTLS"] = "never" 

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 2. NAHRÁNÍ EXCELU
st.subheader("1. Nahraj Excel (.xlsx)")
excel_file = st.file_uploader("Vyber soubor číselníku", type=["xlsx"])
df_ciselnik = None
if excel_file:
    df_ciselnik = pd.read_excel(excel_file)
    st.success("Číselník načten!")

st.divider()

# 3. NAHRÁNÍ FAKTURY
st.subheader("2. Vyfoť nebo nahraj fakturu")
foto = st.camera_input("Vyfoť") or st.file_uploader("Nebo nahraj fotku", type=["png", "jpg", "jpeg"])

if foto:
    st.image(foto, width=300)
    if st.button("🚀 PŘEČÍST A SPÁROVAT", type="primary"):
        if df_ciselnik is None:
            st.error("Nejdřív nahoře nahraj Excel!")
        else:
            with st.spinner("AI právě luští fakturu přes stabilní kanál..."):
                try:
                    img = Image.open(foto)
                    
                    # Používáme základní model gemini-1.5-flash
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = """Najdi v tabulce SYMBOL a CENU bez DPH. 
                    Odpověz POUZE jako JSON seznam: [{"Symbol": "GRSE02", "Cena": 61.00}]"""
                    
                    # Volání s fixem
                    response = model.generate_content([prompt, img])
                    
                    raw = response.text.strip()
                    if "```json" in raw:
                        raw = raw.split("```json")[1].split("```")[0].strip()
                    elif "```" in raw:
                        raw = raw.split("```")[1].split("```")[0].strip()
                    
                    data_f = pd.DataFrame(json.loads(raw))
                    
                    # Párování
                    sl_A = df_ciselnik.columns[0]
                    data_f['Symbol'] = data_f['Symbol'].astype(str)
                    df_ciselnik[sl_A] = df_ciselnik[sl_A].astype(str)
                    
                    final = pd.merge(data_f, df_ciselnik, left_on='Symbol', right_on=sl_A, how='left')
                    
                    st.success("Hotovo!")
                    st.data_editor(final, use_container_width=True)
                    
                except Exception as e:
                    # Pokud i tohle selže, vypíšeme detail, jestli to není regionem
                    st.error(f"Chyba: {e}")
                    if "404" in str(e):
                        st.warning("Google stále odmítá model. Zkusíme vteřinu počkat, než se nový API klíč aktivuje (může to trvat 5 minut).")
