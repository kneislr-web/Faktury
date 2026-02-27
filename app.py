import streamlit as st
import pandas as pd
import requests
import json
import base64

st.set_page_config(page_title="Párování faktur", layout="wide")
st.title("📸 Nouzový režim párování")

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
    if st.button("🚀 ODPÁLIT RUČNÍ PŘIPOJENÍ"):
        if not df_ciselnik:
            st.error("Chybí Excel!")
        else:
            with st.spinner("Posílám data přímo do Googlu (obcházím chybu 404)..."):
                try:
                    # Příprava obrázku pro přímý přenos
                    base64_image = base64.b64encode(foto.read()).decode('utf-8')
                    
                    # Ruční sestavení požadavku (vynucení verze v1)
                    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
                    
                    payload = {
                        "contents": [{
                            "parts": [
                                {"text": "Najdi v tabulce faktury SYMBOL a Cenu. Odpovez POUZE jako JSON seznam: [{'Symbol': '...', 'Cena': 123}]"},
                                {"inline_data": {"mime_type": "image/jpeg", "data": base64_image}}
                            ]
                        }]
                    }
                    
                    response = requests.post(url, json=payload)
                    vysledek = response.json()
                    
                    # Vytáhnutí textu z odpovědi
                    odpoved_text = vysledek['candidates'][0]['content']['parts'][0]['text']
                    clean_json = odpoved_text.replace("```json", "").replace("```", "").strip()
                    
                    data_f = pd.DataFrame(json.loads(clean_json))
                    
                    # Párování
                    sl_A = df_ciselnik.columns[0]
                    data_f['Symbol'] = data_f['Symbol'].astype(str)
                    df_ciselnik[sl_A] = df_ciselnik[sl_A].astype(str)
                    
                    final = pd.merge(data_f, df_ciselnik, left_on='Symbol', right_on=sl_A, how='left')
                    st.success("KONEČNĚ! Máme data.")
                    st.data_editor(final)
                    
                except Exception as e:
                    st.error(f"I ruční pokus selhal. Odpověď serveru: {vysledek if 'vysledek' in locals() else e}")
