import streamlit as st
import pandas as pd
import requests
import json
import base64

st.set_page_config(page_title="Párování Gemini", layout="wide")
st.title("📸 Stabilní režim párování")

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
            with st.spinner("AI právě luští fakturu..."):
                try:
                    base_64_image = base64.b64encode(foto.read()).decode('utf-8')
                    
                    # UNIVERZÁLNÍ URL - toto označení funguje vždy, když je klíč aktivní
                    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
                    
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
                        sl_A = df_ciselnik.columns[0]
                        sl_B = df_ciselnik.columns[1]
                        
                        data_f['Symbol'] = data_f['Symbol'].astype(str).str.strip()
                        df_ciselnik[sl_A] = df_ciselnik[sl_A].astype(str).str.strip()
                        
                        final = pd.merge(data_f, df_ciselnik, left_on='Symbol', right_on=sl_A, how='left')
                        st.success("KONEČNĚ! Data spárována.")
                        st.data_editor(final, use_container_width=True)
                    else:
                        # Pokud to zase hodí 404, vypíšeme SEZNAM dostupných modelů přímo pro tvůj klíč!
                        st.error(f"Chyba: {vysledek.get('error', {}).get('message', 'Neznámá chyba')}")
                        st.info("Zkouším zjistit, jaké modely tvůj klíč vlastně vidí...")
                        list_url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
                        list_res = requests.get(list_url).json()
                        st.write("Tvoje dostupné modely:", list_res)
                        
                except Exception as e:
                    st.error(f"Chyba: {e}")
