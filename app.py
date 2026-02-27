import streamlit as st
import pandas as pd
import requests
import json
import base64

st.set_page_config(page_title="Párování Gemini 2.5", layout="wide")
st.title("🚀 Párování s Gemini 2.5 Flash")

# Načtení klíče
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Chybí API klíč v Secrets!")
    st.stop()

api_key = st.secrets["GEMINI_API_KEY"]

st.subheader("1. Nahraj Excel")
excel_file = st.file_uploader("Soubor .xlsx", type=["xlsx"])
df_ciselnik = None
if excel_file:
    df_ciselnik = pd.read_excel(excel_file)
    st.success("Excel načten!")

st.divider()

st.subheader("2. Vyfoť fakturu")
foto = st.camera_input("Vyfoť") or st.file_uploader("Nahraj fotku", type=["png", "jpg", "jpeg"])

if foto:
    if st.button("🚀 SPUSTIT PÁROVÁNÍ", type="primary"):
        if df_ciselnik is None:
            st.error("Nejdřív nahraj Excel!")
        else:
            with st.spinner("Gemini 2.5 Flash právě luští fakturu..."):
                try:
                    base_64_image = base64.b64encode(foto.read()).decode('utf-8')
                    
                    # TADY JE TA OPRAVA - název přímo z tvého seznamu
                    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
                    
                    payload = {
                        "contents": [{
                            "parts": [
                                {"text": "Najdi v tabulce faktury SYMBOL a Cenu. Odpověz POUZE jako JSON seznam: [{'Symbol': '...', 'Cena': 123.45}]"},
                                {"inline_data": {"mime_type": "image/jpeg", "data": base_64_image}}
                            ]
                        }]
                    }
                    
                    response = requests.post(url, json=payload)
                    vysledek = response.json()
                    
                    if 'candidates' in vysledek:
                        odpoved_text = vysledek['candidates'][0]['content']['parts'][0]['text']
                        clean_json = odpoved_text.replace("```json", "").replace("```", "").strip()
                        
                        data_f = pd.DataFrame(json.loads(clean_json))
                        
                        # Párování
                        sl_A = df_ciselnik.columns[0]
                        data_f['Symbol'] = data_f['Symbol'].astype(str).str.strip()
                        df_ciselnik[sl_A] = df_ciselnik[sl_A].astype(str).str.strip()
                        
                        final = pd.merge(data_f, df_ciselnik, left_on='Symbol', right_on=sl_A, how='left')
                        
                        st.success("HOTOVO! Gemini 2.5 Flash to zvládl.")
                        st.data_editor(final, use_container_width=True)
                    else:
                        st.error(f"Chyba: {vysledek.get('error', {}).get('message', 'Neznámá chyba')}")
                except Exception as e:
                    st.error(f"Chyba: {e}")
