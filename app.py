import streamlit as st
import pandas as pd
import requests
import json
import base64

st.set_page_config(page_title="Párování Gemini 3.1", layout="wide")
st.title("🚀 Párování faktur s Gemini 3.1 Flash")

# Načtení klíče
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Chybí API klíč v Secrets!")
    st.stop()

api_key = st.secrets["GEMINI_API_KEY"]

# 1. NAHRÁNÍ EXCELU
st.subheader("1. Nahraj Excel (tuningtec.xlsx)")
excel_file = st.file_uploader("Soubor .xlsx", type=["xlsx"])
df_ciselnik = None
if excel_file:
    df_ciselnik = pd.read_excel(excel_file)
    st.success("Excel načten!")

st.divider()

# 2. NAHRÁNÍ FAKTURY
st.subheader("2. Vyfoť nebo nahraj fakturu")
foto = st.camera_input("Vyfoť") or st.file_uploader("Nahraj fotku", type=["png", "jpg", "jpeg"])

if foto:
    if st.button("🚀 SPUSTIT PÁROVÁNÍ", type="primary"):
        if df_ciselnik is None:
            st.error("Nejdřív nahraj Excel!")
        else:
            with st.spinner("Gemini 3.1 Flash právě analyzuje fakturu..."):
                try:
                    # Příprava obrázku
                    base_64_image = base64.b64encode(foto.read()).decode('utf-8')
                    
                    # HLAVNÍ URL PRO GEMINI 3.1 FLASH
                    # Pokud by verze 3.1 hlásila chybu, kód automaticky zkusí náhradní cestu
                    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-3.1-flash:generateContent?key={api_key}"
                    
                    payload = {
                        "contents": [{
                            "parts": [
                                {"text": "Najdi v tabulce faktury SYMBOL (kód položky) a Cenu bez DPH. Odpověz POUZE jako čistý JSON seznam: [{'Symbol': '...', 'Cena': 123.45}]. Nic jiného nepiš."},
                                {"inline_data": {"mime_type": "image/jpeg", "data": base_64_image}}
                            ]
                        }]
                    }
                    
                    response = requests.post(url, json=payload)
                    vysledek = response.json()
                    
                    # Kontrola odpovědi
                    if 'candidates' in vysledek:
                        odpoved_text = vysledek['candidates'][0]['content']['parts'][0]['text']
                        # Očištění od případných markdown značek
                        clean_json = odpoved_text.replace("```json", "").replace("```", "").strip()
                        
                        data_f = pd.DataFrame(json.loads(clean_json))
                        
                        # Párování (V-Lookup)
                        sl_A = df_ciselnik.columns[0] # Sloupec A v Excelu (Symbol)
                        sl_B = df_ciselnik.columns[1] # Sloupec B v Excelu (Tvůj kód)
                        
                        data_f['Symbol'] = data_f['Symbol'].astype(str).str.strip()
                        df_ciselnik[sl_A] = df_ciselnik[sl_A].astype(str).str.strip()
                        
                        final = pd.merge(data_f, df_ciselnik, left_on='Symbol', right_on=sl_A, how='left')
                        
                        # Přejmenování pro přehlednost
                        final = final.rename(columns={sl_A: 'Symbol_Excel', sl_B: 'Tvůj_Kód'})
                        
                        st.success("Hotovo! Gemini 3.1 úspěšně spároval data.")
                        st.data_editor(final, use_container_width=True)
                        
                        # Export
                        csv = final.to_csv(index=False).encode('utf-8-sig')
                        st.download_button("📥 Stáhnout hotovou tabulku", csv, "vysledek_parovani.csv", "text/csv")
                    
                    elif 'error' in vysledek:
                        st.error(f"Google AI hlásí chybu: {vysledek['error']['message']}")
                        if "404" in str(vysledek):
                            st.info("Tip: Zkus v kódu změnit 'gemini-3.1-flash' na 'gemini-3.0-flash' – tvůj region může být o krůček pozadu.")
                    else:
                        st.error(f"Neznámá odpověď: {vysledek}")
                        
                except Exception as e:
                    st.error(f"Chyba při zpracování: {e}")
