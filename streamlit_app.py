import streamlit as st
import pandas as pd

# Nastavení stránky (široké rozložení)
st.set_page_config(page_title="Průvodce Akciovými Ukazateli", layout="wide", page_icon="📊")

# Základní URL vaší Google Tabulky (bez parametrů listu)
base_url = "https://docs.google.com/spreadsheets/d/12KhfbhPQtJnlj_987Lo8CT7dUJ0GYSexu7tOunaGLdw"

# Konstrukce URL pro export konkrétních listů do CSV (pomocí gviz rozhraní)
url_data = f"{base_url}/gviz/tq?tqx=out:csv&sheet=Data"
url_kategorie = f"{base_url}/gviz/tq?tqx=out:csv&sheet=Kategorie"

# Načtení dat s kešováním
@st.cache_data
def load_all_data(url_d, url_k):
    try:
        df_d = pd.read_csv(url_d)
        df_k = pd.read_csv(url_k)
        
        # 1. Vyčištění názvů sloupců od neviditelných mezer
        df_d.columns = df_d.columns.str.strip()
        df_k.columns = df_k.columns.str.strip()
        
        # 2. Vyčištění textových hodnot v klíčových sloupcích (prevence chyb při kopírování)
        for col in df_d.columns:
            if df_d[col].dtype == 'object':
                df_d[col] = df_d[col].astype(str).str.strip()
                
        for col in df_k.columns:
            if df_k[col].dtype == 'object':
                df_k[col] = df_k[col].astype(str).str.strip()
        
        # Ošetření ID jako čísel
        if 'ID' in df_d.columns:
            df_d['ID'] = pd.to_numeric(df_d['ID'], errors='coerce')
            
        return df_d, df_k
    except Exception as e:
        st.error(f"Nepodařilo se načíst data z Google Tabulky. Chyba: {e}")
        return None, None

df_data, df_kat = load_all_data(url_data, url_kategorie)

# Inicializace stavu aplikace (Session State) pro navigaci mezi přehledem a detailem
if "zvolena_zkratka" not in st.session_state:
    st.session_state.zvolena_zkratka = None

if df_data is not None and df_kat is not None:
    
    # --- SIDEBAR NAVIGACE ---
    st.sidebar.header("🔍 Rychlá navigace")
    
    # Výběr kategorie v sidebaru
    kategorie_list = ["Všechny"] + list(df_data["Kategorie"].dropna().unique())
    sidebar_kat = st.sidebar.selectbox("Filtrovat podle kategorie:", kategorie_list, key="sidebar_kat_val")

    if sidebar_kat != "Všechny":
        filtr_sidebar_df = df_data[df_data["Kategorie"] == sidebar_kat]
    else:
        filtr_sidebar_df = df_data

    # Výběr konkrétního ukazatele v sidebaru
    filtr_sidebar_df = filtr_sidebar_df.sort_values(by="Zkratka")
    ukazatel_list = ["-- Vyberte --"] + list(filtr_sidebar_df["Zkratka"].dropna().unique())
    
    # Synchronizace sidebaru se stavem aplikace
    index_select = 0
    if st.session_state.zvolena_zkratka in ukazatel_list:
        index_select = ukazatel_list.index(st.session_state.zvolena_zkratka)
        
    sidebar_ukazatel = st.sidebar.selectbox("Přejít na ukazatel:", ukazatel_list, index=index_select)
    
    # Pokud uživatel vybere něco v sidebaru, aktualizujeme stav
    if sidebar_ukazatel != "-- Vyberte --":
        st.session_state.zvolena_zkratka = sidebar_ukazatel
    elif sidebar_ukazatel == "-- Vyberte --" and st.session_state.zvolena_zkratka is not None:
        # Uživatel resetoval výběr v sidebaru
        if sidebar_kat != "Všechny" and df_data[df_data["Zkratka"] == st.session_state.zvolena_zkratka]["Kategorie"].iloc[0] != sidebar_kat:
            st.session_state.zvolena_zkratka = None


    # --- HLAVNÍ PLOCHA APLIKACE ---
    
    # SCÉNÁŘ 1: JE VYBRÁN KONKRÉTNÍ UKAZATEL (ZOBRAZÍME DETAIL)
    if st.session_state.zvolena_zkratka is not None:
        # Tlačítko zpět na hlavní přehled
        if st.button("⬅️ Zpět na hlavní přehled"):
            st.session_state.zvolena_zkratka = None
            st.rerun()
            
        # Načtení dat pro vybraný ukazatel
        row = df_data[df_data["Zkratka"] == st.session_state.zvolena_zkratka].iloc[0]
        current_id = row['ID']

        st.header(f"{row['Ukazatel']} ({row['Zkratka']})")
        st.caption(f"Kategorie: {row['Kategorie']} | ID kód v databázi: {int(current_id) if pd.notnull(current_id) else 'N/A'}")
        st.markdown("---")

        # Vzorec
        st.subheader("🧮 Vzorec / Konstrukce")
        st.info(f"**{row['Vzorec']}**")

        # Charakteristika a Interpretace
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 💡 Co představuje?")
            st.write(row["Hlavni_Charakteristika"])
        with col2:
            st.markdown("### 🔍 Jak ho číst a interpretovat?")
            st.write(row["Jak_Interpretovat"])

        st.markdown("---")

        # Hodnoty
        st.subheader("📈 Vodítko k posouzení hodnot")
        col3, col4 = st.columns(2)
        with col3:
            st.success(f"**Optimální / Obvyklé hodnoty:**\n\n{row['Optimalni_Hodnoty']}")
        with col4:
            st.error(f"**Kritické / Rizikové hodnoty:**\n\n{row['Kriticke_Hodnoty']}")

        st.markdown("---")

        # Kalkulačka
        st.subheader("🧮 Interaktivní kalkulačka")
        with st.expander(f"Otevřít kalkulačku pro: {row['Zkratka']}", expanded=False):
            if row['Zkratka'] == 'P/E':
                calc_price = st.number_input("Aktuální cena akcie:", min_value=0.0, value=150.0, step=1.0)
                calc_eps = st.number_input("Zisk na akcii (EPS):", min_value=0.01, value=7.5, step=0.1)
                result_pe = calc_price / calc_eps
                st.metric(label="Výsledné P/E", value=f"{result_pe:.2f}")
                if result_pe > 30: st.warning("⚠️ Hodnota P/E je vysoká. Trh očekává velký budoucí růst.")
                elif result_pe < 10: st.info("ℹ️ Hodnota P/E je nízká. Může jít o podhodnocení či hodnotovou past.")
                else: st.success("✅ Hodnota P/E se pohybuje v běžném průměru.")
            elif row['Zkratka'] == 'Net Margin':
                calc_profit = st.number_input("Čistý zisk po zdanění (EAT):", min_value=0.0, value=150000.0, step=1000.0)
                calc_sales = st.number_input("Celkové tržby (Sales):", min_value=1.0, value=1000000.0, step=1000.0)
                result_margin = (calc_profit / calc_sales) * 100
                st.metric(label="Čistá marže", value=f"{result_margin:.2f} %")
                if result_margin > 15: st.success("✅ Skvělá marže! Silná konkurenční výhoda.")
                elif result_margin < 5: st.error("⚠️ Nízká marže. Byznys je zranitelný vůči růstu nákladů.")
            else:
                st.write(f"Pro ukazatel **{row['Zkratka']}** se kalkulačka připravuje podle vzorce: `{row['Vzorec']}`.")

        st.markdown("---")

        # Vazby
        st.subheader("🔗 Vazby na jiné ukazatele a kontext")
        vazby_raw = str(row["Vazby_Na_Jine_Ukazatele"]).strip()
        if vazby_raw and vazby_raw != "nan" and vazby_raw != "":
            try:
                id_list = [int(x.strip()) for x in vazby_raw.split(",") if x.strip().isdigit()]
                if id_list:
                    for target_id in id_list:
                        target_row = df_data[df_data['ID'] == target_id]
                        if not target_row.empty:
                            target_data = target_row.iloc[0]
                            # Vytvoření odkazu pomocí st.button s unikátním klíčem
                            if st.button(f"➡️ {target_data['Zkratka']} – {target_data['Ukazatel']}", key=f"link_{target_id}"):
                                st.session_state.zvolena_zkratka = target_data['Zkratka']
                                st.rerun()
                else: st.warning(vazby_raw)
            except: st.warning(vazby_raw)
        else: st.info("Pro tento ukazatel zatím nebyly definovány specifické vazby.")


    # SCÉNÁŘ 2: NENÍ VYBRÁN UKAZATEL (ZOBRAZÍME ROZCESTNÍK / MŘÍŽKU 6 PANELŮ)
    else:
        st.title("🗂️ Rozcestník investičních ukazatelů")
        st.write("Klikněte na jakoukoli kategorii pro zobrazení podrobností, nebo rovnou klikněte na nejdůležitější zkratky.")
        st.markdown("<br>", unsafe_allowed_html=True)

        # Definice 6 panelů v mřížce 3 sloupce × 2 řádky
        row1_col1, row1_col2, row1_col3 = st.columns(3)
        row2_col1, row2_col2, row2_col3 = st.columns(3)

        mrizka = [
            {"panel": row1_col1, "kat_nazev": "Výsledovka"},
            {"panel": row1_col2, "kat_nazev": "Rozvaha"},
            {"panel": row1_col3, "kat_nazev": "Finanční zdraví"},
            {"panel": row2_col1, "kat_nazev": "Valuace"},
            {"panel": row2_col2, "kat_nazev": "Makroekonomie"},
            {"panel": row2_col3, "kat_nazev": "Makro / Sentiment"}
        ]

        for radek in mrizka:
            with radek["panel"]:
                # Vytvoření vizuálního ohraničeného kontejneru pro každý panel
                with st.container(border=True):
                    st.markdown(f"### 📂 {radek['kat_nazev']}")
                    
                    # Načtení úvodního textu z druhého listu 'Kategorie'
                    kat_info = df_kat[df_kat["Nazev_Kategorie"] == radek["kat_nazev"]]
                    if not kat_info.empty:
                        st.write(kat_info["Uvodni_Text"].iloc[0][:140] + "...") # Zkrácený náhled textu
                    
                    st.markdown("**Hlavní ukazatele (Rychlý odkaz):**")
                    
                    # Vyhledání hlavních ukazatelů z dané kategorie (kde Hlavni_Ukazatel == 'ANO')
                    if "Hlavni_Ukazatel" in df_data.columns:
                        hlavni_ukazatele = df_data[
                            (df_data["Kategorie"] == radek["kat_nazev"]) & 
                            (df_data["Hlavni_Ukazatel"].astype(str).str.strip().str.upper() == "ANO")
                        ]
                    else:
                        hlavni_ukazatele = pd.DataFrame()
                    
                    # Bezpečnostní kontrola: Sloupce tvoříme jen tehdy, pokud máme aspoň jeden hlavni ukazatel
                    if not hlavni_ukazatele.empty and len(hlavni_ukazatele) > 0:
                        cols_buttons = st.columns(len(hlavni_ukazatele))
                        for idx, (_, u_row) in enumerate(hlavni_ukazatele.iterrows()):
                            with cols_buttons[idx]:
                                if st.button(u_row["Zkratka"], key=f"main_grid_{u_row['Zkratka']}", help=u_row["Ukazatel"]):
                                    st.session_state.zvolena_zkratka = u_row["Zkratka"]
                                    st.rerun()
                    else:
                        st.caption("Žádné hlavní ukazatele nebyly označeny.")
                    
                    # Tlačítko pro rozbalení celé legendy a všech ukazatelů kategorie
                    with st.expander("Zobrazit celou kategorii", expanded=False):
                        if not kat_info.empty:
                            st.write(kat_info["Uvodni_Text"].iloc[0])
                            if "Co_Zde_Najdete" in df_kat.columns:
                                st.markdown(f"**Co zde najdete:** {kat_info['Co_Zde_Najdete'].iloc[0]}")
                        
                        st.markdown("**Všechny položky této kategorie:**")
                        vsechny_kat_polozky = df_data[df_data["Kategorie"] == radek["kat_nazev"]].sort_values(by="Zkratka")
                        for _, p_row in vsechny_kat_polozky.iterrows():
                            if st.button(f"🔍 {p_row['Zkratka']} - {p_row['Ukazatel']}", key=f"expander_list_{p_row['Zkratka']}"):
                                st.session_state.zvolena_zkratka = p_row["Zkratka"]
                                st.rerun()

else:
    st.info("Zkontrolujte, zda jsou listy 'Data' a 'Kategorie' ve vaší Google Tabulce správně pojmenované.")
