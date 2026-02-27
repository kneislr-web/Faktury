import streamlit as st
import pandas as pd
import requests
import json
import base64

st.set_page_config(page_title="Párování faktur", layout="wide")
st.title("📸 Ruční režim párování")

# Načtení klíče ze Secrets
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
    if st.button("🚀 ODPÁLIT RUČNÍ PŘIPOJENÍ", type="primary"):
        if df_ciselnik is None:
            st.error("Nejdřív nahoře nahraj ten Excel!")
        else:
            with st.spinner("Posílám fotku přímo do Googlu..."):
                try:
                    # Příprava obrázku
                    base_64_image = base64.b64encode(foto.read()).decode('utf-8')
                    
                    # URL pro stabilní verzi v1
                    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
                    
                    payload = {
                        "contents": [{
                            "parts": [
                                {"text": "Najdi v tabulce faktury SYMBOL a Cenu. Odpovez POUZE jako JSON seznam objektů, nic jiného. Příklad: [{'Symbol': 'GRSE02', 'Cena': 61.00}]"},
                                {"inline_data": {"mime_type": "image/jpeg", "data": base_64_image}}
                            ]
                        }]
                    }
                    
                    response = requests.post(url, json=payload)
                    vysledek = response.json()
                    
                    # Kontrola, jestli nám Google něco vrátil
                    if 'candidates' in vysledek:
                        odpoved_text = vysledek['candidates'][0]['content']['parts'][0]['text']
                        clean_json = odpoved_text.replace("```json", "").replace("```", "").strip()
                        
                        data_f = pd.DataFrame(json.loads(clean_json))
                        
                        # Párování (V-Lookup)
                        sl_A = df_ciselnik.columns[0]
                        data_f['Symbol'] = data_f['Symbol'].astype(str)
                        df_ciselnik[sl_A] = df_ciselnik[sl_A].astype(str)
                        
                        final = pd.merge(data_f, df_ciselnik, left_on='Symbol', right_on=sl_A, how='left')
                        
                        st.success("KONEČNĚ! Tady jsou spárovaná data:")
                        st.data_editor(final, use_container_width=True)
                        
                        csv = final.to_csv(index=False).encode('utf-8-sig')
                        st.download_button("📥 Stáhnout výsledek", csv, "vysledek.csv", "text/csv")
                    else:
                        st.error(f"Google neodpověděl správně. Odpověď: {vysledek}")
                        
                except Exception as e:
                    st.error(f"Chyba: {e}")
