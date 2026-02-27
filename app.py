import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
from PIL import Image

st.set_page_config(page_title="Zpracování faktur", layout="wide")
st.title("📸 Chytré párování faktur s AI")

try:
  genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
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

if st.button("🚀 Přečíst fakturu a spárovat s Excelem", type="primary"):
  if df_ciselnik is None:
    st.warning("Nejdřív nahoře nahraj svůj Excel (číselník), abych měl data s čím spárovat!")
else:
    with st.spinner("Umělá inteligence teď luští fakturu... Může to trvat 10-20 vteřin..."):
        try:
            img = Image.open(foto)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')

            prompt = """
            Jsi expert na čtení faktur. Najdi na obrázku tabulku s položkami.
            Pro každou položku najdi:
            1. 'Symbol' (např. kód jako GRSE02, často ve sloupci Symbol nebo Kód).
            2. 'Cenu' (cena bez DPH nebo částka za položku).

            Odpověz POUZE v čistém formátu JSON jako seznam objektů. Nepiš žádný text okolo.
            Příklad:
            [
            {"Symbol": "GRSE02", "Cena": "61.00"}
            ]
            """

            response = model.generate_content([prompt, img])
            vysledek_text = response.text.strip()

            # --- VŠECHNY TYTO ŘÁDKY MUSÍ BÝT ODSZENÉ DOPRAVA ---
            if vysledek_text.startswith("```json"):
                vysledek_text = vysledek_text[7:-3].strip()
            elif vysledek_text.startswith("```"):
                vysledek_text = vysledek_text[3:-3].strip()

            data_faktura = json.loads(vysledek_text)
            df_faktura = pd.DataFrame(data_faktura)

            sloupec_A = df_ciselnik.columns[0]
            sloupec_B = df_ciselnik.columns[1]

            df_faktura['Symbol'] = df_faktura['Symbol'].astype(str)
            df_ciselnik[sloupec_A] = df_ciselnik[sloupec_A].astype(str)

            vysledna_tabulka = pd.merge(df_faktura, df_ciselnik, left_on='Symbol', right_on=sloupec_A, how='left')

            vysledna_tabulka = vysledna_tabulka[['Symbol', sloupec_B, 'Cena']]
            vysledna_tabulka.columns = ['Symbol z faktury', 'Tvůj kód', 'Cena (bez DPH)']

            st.success("Úspěšně přečteno a spárováno!")
            upravena_data = st.data_editor(vysledna_tabulka, num_rows="dynamic")

            st.download_button(
                label="📥 Stáhnout data pro účetní (CSV)",
                data=upravena_data.to_csv(index=False).encode('utf-8'),
                file_name="zpracovana_faktura.csv",
                mime="text/csv",
            )
            # --------------------------------------------------

        except Exception as e:
            st.error(f"Něco se nepovedlo přečíst. Detail chyby: {e}")
