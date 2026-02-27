import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
from PIL import Image

st.set_page_config(page_title="Párování faktur", layout="wide")
st.title("📸 Chytré párování faktur")

# 1. NASTAVENÍ API - POUŽÍVÁME STABILNÍ VERZI
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Chybí API klíč v Secrets!")
    st.stop()

# Konfigurace klíče
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 2. NAHRÁNÍ EXCELU
st.subheader("1. Nahraj Excel")
excel_file = st.file_uploader("Vyber soubor .xlsx", type=["xlsx"])
df_ciselnik = None
if excel_file:
    df_ciselnik = pd.read_excel(excel_file)
    st.success("Excel (číselník) načten!")

st.divider()

# 3. NAHRÁNÍ FAKTURY
st.subheader("2. Vyfoť nebo nahraj fakturu")
foto = st.camera_input("Vyfoť") or st.file_uploader("Nahraj obrázek", type=["png", "jpg", "jpeg"])

if foto:
    st.image(foto, width=350)
    if st.button("🚀 PŘEČÍST A SPÁROVAT", type="primary"):
        if df_ciselnik is None:
            st.error("Nejdřív nahoře nahraj ten Excel!")
        else:
            with st.spinner("AI čte fakturu..."):
                try:
                    img = Image.open(foto)
                    
                    # TADY JE TA OPRAVA: Vynutíme model bez prefixu 'models/' a verzi flash
                    model = genai.GenerativeModel('gemini-1.5-flash-latest')
                    
                    prompt = """Jsi expert na faktury. Najdi v tabulce SYMBOL a CENU (za kus nebo celkem bez DPH). 
                    Odpověz POUZE jako JSON seznam objektů, nic jiného. 
                    Příklad: [{"Symbol": "GRSE02", "Cena": 61.00}]"""
                    
                    # Generování obsahu
                    response = model.generate_content([prompt, img])
                    
                    # Čištění textu od markdownu
                    res_text = response.text.strip()
                    if "```json" in res_text:
                        res_text = res_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in res_text:
                        res_text = res_text.split("```")[1].split("```")[0].strip()
                    
                    data_z_faktury = json.loads(res_text)
                    df_faktura = pd.DataFrame(data_z_faktury)
                    
                    # PÁROVÁNÍ (V-LOOKUP)
                    # Předpokládáme: Sloupec 1 v Excelu = SYMBOL, Sloupec 2 = TVŮJ KÓD
                    sl_A = df_ciselnik.columns[0]
                    sl_B = df_ciselnik.columns[1]
                    
                    df_faktura['Symbol'] = df_faktura['Symbol'].astype(str)
                    df_ciselnik[sl_A] = df_ciselnik[sl_A].astype(str)
                    
                    final = pd.merge(df_faktura, df_ciselnik, left_on='Symbol', right_on=sl_A, how='left')
                    
                    st.success("Hotovo!")
                    # Zobrazíme přehlednou tabulku
                    st.data_editor(final, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Chyba: {e}")
                    st.info("Tip: Pokud chyba přetrvává, zkus v Google AI Studiu vytvořit nový API klíč.")
