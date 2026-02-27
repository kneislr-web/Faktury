import streamlit as st
import pandas as pd
import requests
import json
import base64

st.set_page_config(page_title="Párování Gemini 3.0", layout="wide")
st.title("🚀 Párování faktur s Gemini 3.0 Flash")

# Načtení klíče ze Secrets
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Chybí API klíč v Secrets! Zkontroluj nastavení v Dashboardu.")
    st.stop()

api_key = st.secrets["GEMINI_API_KEY"]

# 1. NAHRÁNÍ EXCELU
st.subheader("1. Nahraj Excel (číselník)")
excel_file = st.file_uploader("Vyber soubor .xlsx", type=["xlsx"])
df_ciselnik = None
if excel_file:
    df_ciselnik = pd.read_excel(excel_file)
    st.success("Excel úspěšně načten!")

st.divider()

# 2. NAHRÁNÍ FAKTURY
st.subheader("2. Vyfoť nebo nahraj fakturu")
foto = st.camera_input("Vyfoť fakturu") or st.file_uploader("Nebo nahraj fotku", type=["png", "jpg", "jpeg"])

if foto:
    st.image(foto, width=300, caption="Nahraná faktura")
    if st.button("🚀 SPUSTIT PÁROVÁNÍ", type="primary"):
        if df_ciselnik is None:
            st.error("Chybí Excel! Prosím, nahraj ho nejdříve v kroku 1.")
        else:
            with st.spinner("Gemini 3.0 Flash luští fakturu..."):
                try:
                    # Příprava obrázku pro API
                    base_64_image = base64.b64encode(foto.read()).decode('utf-8')
                    
                    # URL pro model Gemini 3.0 Flash
                    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-3.0-flash:generateContent?key={api_key}"
                    
                    payload = {
                        "contents": [{
                            "parts": [
                                {"text": "Najdi v tabulce faktury SYMBOL (kód položky) a Cenu bez DPH. Odpověz POUZE jako JSON seznam: [{'Symbol': '...', 'Cena': 123.45}]. Nic jiného nepiš."},
                                {"inline_data": {"mime_type": "image/jpeg", "data": base_64_image}}
                            ]
                        }]
                    }
                    
                    response = requests.post(url, json=payload)
                    vysledek = response.json()
                    
                    if 'candidates' in vysledek:
                        odpoved_text = vysledek['candidates'][0]['content']['parts'][0]['text']
                        # Odstranění markdown značek ```json a ```
                        clean_json = odpoved_text.replace("```json", "").replace("```", "").strip()
                        
                        data_f = pd.DataFrame(json.loads(clean_json))
                        
                        # Párování dat
                        sl_A = df_ciselnik.columns[0] # Symbol v Excelu
                        sl_B = df_ciselnik.columns[1] # Tvůj kód v Excelu
                        
                        # Vyčištění textových řetězců (odstranění mezer)
                        data_f['Symbol'] = data_f['Symbol'].astype(str).str.strip()
                        df_ciselnik[sl_A] = df_ciselnik[sl_A].astype(str).str.strip()
                        
                        # Samotné spárování (Left Join)
                        final = pd.merge(data_f, df_ciselnik, left_on='Symbol', right_on=sl_A, how='left')
                        
                        # Úprava názvů sloupců
                        final = final.rename(columns={sl_A: 'Nalezený Symbol', sl_B: 'Tvůj Kód z Excelu'})
                        
                        st.success("Hotovo! Data byla spárována pomocí Gemini 3.0.")
                        st.data_editor(final, use_container_width=True)
                        
                        # Tlačítko pro stažení výsledku
                        csv = final.to_csv(index=False).encode('utf-8-sig')
                        st.download_button("📥 Stáhnout hotovou tabulku (CSV)", csv, "vysledek_parovani.csv", "text/csv")
                    
                    elif 'error' in vysledek:
                        st.error(f"Chyba od Googlu: {vysledek['error']['message']}")
                    else:
                        st.error(f"Nečekaná odpověď: {vysledek}")
                        
                except Exception as e:
                    st.error(f"Něco se nepovedlo: {e}")
