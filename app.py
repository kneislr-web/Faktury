import streamlit as st
import pandas as pd

st.set_page_config(page_title="Zpracování faktur", layout="wide")

st.title("📸 Chytré párování faktur")

# 1. Nahrání Excelu (Číselníku)
st.subheader("1. Nahraj svůj číselník (Excel)")
excel_file = st.file_uploader("Vyber soubor .xlsx se svými kódy (Sloupec A = z faktury, Sloupec B = tvůj kód)", type=["xlsx"])

if excel_file:
    # Tady se načte ten tvůj Excel
    df_ciselnik = pd.read_excel(excel_file)
    st.success("Číselník je úspěšně nahraný a připravený!")
    with st.expander("Zobrazit načtený číselník"):
        st.dataframe(df_ciselnik)

st.divider()

# 2. Focení / Nahrání faktury
st.subheader("2. Vyfoť nebo nahraj fakturu")
tab1, tab2 = st.tabs(["📷 Vyfotit mobilem", "📁 Nahrát soubor z PC"])

with tab1:
    foto = st.camera_input("Vyfoť fakturu")
with tab2:
    soubor = st.file_uploader("Nebo nahraj fotku / PDF faktury", type=["png", "jpg", "jpeg", "pdf"])

if foto or soubor:
    st.info("Zpracovávám obrázek a hledám položky... (V další fázi sem přidáme umělou inteligenci na čtení textu)")
    
    # 3. Ukázka výsledku (Historie a úpravy)
    st.subheader("3. Výsledek a úpravy")
    st.write("Zde můžeš překontrolovat načtené hodnoty a případně je upravit:")
    
    # Zatím ukázková data, abys viděl, jak to bude vypadat, než napojíme čtení z fotky
    ukazkova_data = pd.DataFrame({
        "Název/Kód z faktury": ["Hřebíky 50mm", "Kladivo"],
        "Množství": [10, 1],
        "Cena bez DPH (po slevě)": [150.50, 450.00],
        "Tvůj spárovaný kód": ["MAT-001", "NAR-005"]
    })
    
    # Zobrazí se tabulka, kterou můžeš rovnou editovat!
    upravena_data = st.data_editor(ukazkova_data, num_rows="dynamic")
    
    # Tlačítko pro export
    st.download_button(
        label="📥 Stáhnout výsledek pro účetní (CSV)",
        data=upravena_data.to_csv(index=False).encode('utf-8'),
        file_name="zpracovana_faktura.csv",
        mime="text/csv",
    )
