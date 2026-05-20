import streamlit as st
import pandas as pd

# Nastavení stránky (široké rozložení)
st.set_page_config(page_title="Průvodce Akciovými Ukazateli", layout="wide", page_icon="📊")

# URL vaší Google Tabulky (přesný odkaz, který jste poslal)
spreadsheet_url = "https://docs.google.com/spreadsheets/d/12KhfbhPQtJnlj_987Lo8CT7dUJ0GYSexu7tOunaGLdw/edit?gid=96365177#gid=96365177"

# Úprava URL, aby Google Sheets vrátil čistá CSV data pro Pandas
if "edit?usp=sharing" in spreadsheet_url:
    csv_url = spreadsheet_url.replace("edit?usp=sharing", "export?format=csv")
elif "edit#" in spreadsheet_url:
    csv_url = spreadsheet_url.split("edit#")[0] + "export?format=csv"
elif "edit?" in spreadsheet_url:
    csv_url = spreadsheet_url.split("edit?")[0] + "export?format=csv"
else:
    csv_url = spreadsheet_url.rstrip("/") + "/export?format=csv"

# Načtení dat (s kešováním, aby se tabulka nestahovala při každém kliknutí)
@st.cache_data
def load_data(url):
    try:
        df = pd.read_csv(url)
        # Očištění názvů sloupců od případných mezer
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Nepodařilo se načíst data z Google Tabulky. Chyba: {e}")
        return None

df = load_data(csv_url)

# Hlavní nadpis aplikace
st.title("📊 Průvodce Akciovými Ukazateli")
st.write("Interaktivní manuál pro interpretaci fundamentálních poměrových ukazatelů.")

if df is not None:
    # 1. Boční panel (Sidebar) pro výběr kategorie
    kategorie_list = ["Všechny"] + list(df["Kategorie"].unique())
    zvolena_kategorie = st.sidebar.selectbox("Vyberte kategorií ukazatelů:", kategorie_list)

    # Filtrování dat podle kategorie
    if zvolena_kategorie != "Všechny":
        filtr_df = df[df["Kategorie"] == zvolena_kategorie]
    else:
        filtr_df = df

    # 2. Boční panel - výběr konkrétního ukazatele z filtrovaného seznamu
    ukazatel_list = list(filtr_df["Zkratka"].unique())
    zvoleny_ukazatel = st.sidebar.selectbox("Vyberte konkrétní ukazatel:", ukazatel_list)

    # Získání dat vybraného ukazatele (jako jeden řádek / dict)
    row = filtr_df[filtr_df["Zkratka"] == zvoleny_ukazatel].iloc[0]

    # 3. Zobrazení detailu ukazatele na hlavní ploše
    st.header(f"{row['Ukazatel']} ({row['Zkratka']})")
    st.caption(f"Kategorie: {row['Kategorie']}")

    # Vzorec v boxu
    st.subheader("🧮 Vzorec")
    st.info(f"**{row['Vzorec']}**")

    # Hlavní charakteristika a interpretace ve sloupcích
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💡 Co představuje?")
        st.write(row["Hlavni_Charakteristika"])
    with col2:
        st.subheader("🔍 Jak ho číst a interpretovat?")
        st.write(row["Jak_Interpretovat"])

    # Hodnoty (Optimální vs Kritické)
    st.subheader("📈 Vodítko k posouzení hodnot")
    col3, col4 = st.columns(2)
    with col3:
        st.success(f"**Optimální / Obvyklé hodnoty:**\n\n{row['Optimalni_Hodnoty']}")
    with col4:
        st.error(f"**Kritické / Rizikové hodnoty:**\n\n{row['Kriticke_Hodnoty']}")

    # Vazby na jiné ukazatele
    st.subheader("🔗 Vazby na jiné ukazatele a kontext")
    st.warning(row["Vazby_Na_Jine_Ukazatele"])

else:
    st.info("Zkontrolujte, zda je vaše Google Tabulka nasdílená pro 'Všichni, kdo mají odkaz' jako Čtenář.")
