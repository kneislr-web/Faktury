import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
from PIL import Image

st.set_page_config(page_title="Párování faktur", layout="wide")
st.title("📸 Poslední pokus o spojení s AI")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Chybí API klíč v Secrets!")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

st.subheader("1. Nahraj Excel")
excel_file = st.file_uploader("Soubor .xlsx", type=["xlsx"])
df_ciselnik = None
if excel_file:
    df_ciselnik = pd.read_excel(excel_file)
    st.success("Excel načten!")

st.divider()

st.subheader("2. Nahraj fakturu")
foto = st.camera_input("Vyfoť") or st.file_uploader("Nahraj fotku", type=["png", "jpg", "jpeg"])

if foto:
    st.image(foto, width=300)
    if st.button("🚀 ODPÁLIT PÁROVÁNÍ", type="primary"):
        if df_ciselnik is None:
            st.error("Chybí Excel!")
        else:
            with st.spinner("Zkouším se probojovat ke Google AI..."):
                # Zkusíme postupně tyto modely, dokud jeden neprojde
                modely_ke_zkousce = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro-vision']
                uspech = False
                
                for nazev_modelu in modely_ke_zkousce:
                    try:
                        img = Image.open(foto)
                        model = genai.GenerativeModel(nazev_modelu)
                        prompt = "Najdi SYMBOL a Cenu. Odpovez jen JSON: [{'Symbol': '...', 'Cena': 123}]"
                        
                        response = model.generate_content([prompt, img])
                        raw = response.text.strip().replace("```json", "").replace("```", "").strip()
                        
                        data_f = pd.DataFrame(json.loads(raw))
                        sl_A = df_ciselnik.columns[0]
                        data_f['Symbol'] = data_f['Symbol'].astype(str)
                        df_ciselnik[sl_A] = df_ciselnik[sl_A].astype(str)
                        
                        final = pd.merge(data_f, df_ciselnik, left_on='Symbol', right_on=sl_A, how='left')
                        st.success(f"Úspěch s modelem: {nazev_modelu}!")
                        st.data_editor(final)
                        uspech = True
                        break # Pokud se povedlo, končíme cyklus
                    except Exception as e:
                        st.warning(f"Model {nazev_modelu} selhal: {e}")
                        continue # Zkusíme další model
                
                if not uspech:
                    st.error("Žádný z modelů Google AI není pro tvůj klíč momentálně dostupný. Zkontroluj regionální nastavení v Google AI Studiu.")
