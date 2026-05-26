import streamlit as st
import pandas as pd

# Nastavení stránky (široké rozložení)
st.set_page_config(page_title="Průvodce Akciovými Ukazateli", layout="wide", page_icon="📊")

# Základní URL vaší Google Tabulky
base_url = "https://docs.google.com/spreadsheets/d/12KhfbhPQtJnlj_987Lo8CT7dUJ0GYSexu7tOunaGLdw"
url_data = f"{base_url}/gviz/tq?tqx=out:csv&sheet=Data"
url_kategorie = f"{base_url}/gviz/tq?tqx=out:csv&sheet=Kategorie"

@st.cache_data
def load_all_data(url_d, url_k):
    try:
        df_d = pd.read_csv(url_d)
        df_k = pd.read_csv(url_k)
        df_d.columns = df_d.columns.str.strip()
        df_k.columns = df_k.columns.str.strip()
        
        for col in df_d.columns:
            if df_d[col].dtype == 'object':
                df_d[col] = df_d[col].astype(str).str.strip()
        for col in df_k.columns:
            if df_k[col].dtype == 'object':
                df_k[col] = df_k[col].astype(str).str.strip()
        
        if 'ID' in df_d.columns:
            df_d['ID'] = pd.to_numeric(df_d['ID'], errors='coerce')
        return df_d, df_k
    except Exception as e:
        st.error(f"Nepodařilo se načíst data. Chyba: {e}")
        return None, None

df_data, df_kat = load_all_data(url_data, url_kategorie)

# Inicializace stavů v Session State
if "zvolena_zkratka" not in st.session_state:
    st.session_state.zvolena_zkratka = None
if "historie_navigace" not in st.session_state:
    st.session_state.historie_navigace = []

# Pomocná funkce pro bezpečnou změnu ukazatele z plochy
def prejit_na_ukazatel(nova_zkratka):
    if st.session_state.zvolena_zkratka and st.session_state.zvolena_zkratka != nova_zkratka:
        if st.session_state.zvolena_zkratka not in st.session_state.historie_navigace:
            st.session_state.historie_navigace.append(st.session_state.zvolena_zkratka)
    st.session_state.zvolena_zkratka = nova_zkratka

if df_data is not None and df_kat is not None:
    
    # --- SIDEBAR NAVIGACE ---
    st.sidebar.header("🔍 Rychlá navigace")
    
    kategorie_list = ["Všechny"] + list(df_data["Kategorie"].dropna().unique())
    sidebar_kat = st.sidebar.selectbox("Filtrovat podle kategorie:", kategorie_list, key="sidebar_kat_val")

    if sidebar_kat != "Všechny":
        filtr_sidebar_df = df_data[df_data["Kategorie"] == sidebar_kat]
    else:
        filtr_sidebar_df = df_data

    filtr_sidebar_df = filtr_sidebar_df.sort_values(by="Zkratka")
    ukazatel_list = ["-- Vyberte --"] + list(filtr_sidebar_df["Zkratka"].dropna().unique())
    
    index_select = 0
    if st.session_state.zvolena_zkratka in ukazatel_list:
        index_select = ukazatel_list.index(st.session_state.zvolena_zkratka)
        
    vyber_sidebar = st.sidebar.selectbox(
        "Přejít na ukazatel:", 
        ukazatel_list, 
        index=index_select, 
        key="selectbox_ukazatel_sidebar"
    )

    # Detekce ruční změny v sidebaru bez callbacku
    if vyber_sidebar == "-- Vyberte --":
        if st.session_state.zvolena_zkratka is not None:
            st.session_state.zvolena_zkratka = None
            st.session_state.historie_navigace = []
            st.rerun()
    elif vyber_sidebar != st.session_state.zvolena_zkratka:
        prejit_na_ukazatel(vyber_sidebar)
        st.rerun()

    # --- HLAVNÍ PLOCHA APLIKACE ---
    
    # SCÉNÁŘ 1: DETAIL UKAZATELE
    if st.session_state.zvolena_zkratka is not None:
        
        # KOMPAKTNÍ LIŠTA: Tlačítka těsně vedle sebe
        nav_col1, nav_col2, _ = st.columns([1.2, 2.2, 8.6])
        with nav_col1:
            if st.button("⬅️ Zpět", disabled=len(st.session_state.historie_navigace) == 0):
                st.session_state.zvolena_zkratka = st.session_state.historie_navigace.pop()
                st.rerun()
        with nav_col2:
            if st.button("🏠 Hlavní přehled"):
                st.session_state.zvolena_zkratka = None
                st.session_state.historie_navigace = []
                st.rerun()
            
        row = df_data[df_data["Zkratka"] == st.session_state.zvolena_zkratka].iloc[0]
        current_id = row['ID']

        # Hlavní nadpis
        st.subheader(f"📊 {row['Ukazatel']} ({row['Zkratka']})")
        st.caption(f"Kategorie: {row['Kategorie']} | ID: {int(current_id) if pd.notnull(current_id) else 'N/A'}")
        
        # Sekce 1: Vzorec
        st.info(f"**🧮 Vzorec / Konstrukce:** {row['Vzorec']}")

        # Sekce 2: Charakteristika a Interpretace vedle sebe
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**💡 Co představuje?**")
            st.markdown(f"*{row['Hlavni_Charakteristika']}*")
        with col2:
            st.markdown("**🔍 Jak ho číst a interpretovat?**")
            st.markdown(f"*{row['Jak_Interpretovat']}*")

        # Sekce 3: Hodnoty vedle sebe
        col3, col4 = st.columns(2)
        with col3:
            st.success(f"**📈 Optimální / Obvyklé hodnoty:**\n\n{row['Optimalni_Hodnoty']}")
        with col4:
            st.error(f"**📉 Kritické / Rizikové hodnoty:**\n\n{row['Kriticke_Hodnoty']}")

        # Sekce 4: NEPRŮSTŘELNÁ DIAL_UP NAVIGACE PODLE ČISTÝCH ID
        vazby_raw = str(row["Vazby_Na_Jine_Ukazatele"]).strip()
        if vazby_raw and vazby_raw != "nan" and vazby_raw != "":
            id_list = []
            for x in vazby_raw.split(","):
                x_clean = x.strip()
                if x_clean.isdigit():
                    target_id = int(x_clean)
                    if target_id != int(current_id) and target_id not in id_list:
                        id_list.append(target_id)
            
            if id_list:
                st.markdown("**🔗 Související ukazatele:**")
                st.html(
                    """
                    <style>
                        div[data-testid="stHorizontalBlock"] { gap: 10px !important; }
                        div[data-testid="element-container"]:has(div.stButton) {
                            display: inline-block !important; width: auto !important; flex: none !important;
                        }
                    </style>
                    """
                )
                cols_vazby = st.columns([1] * len(id_list) + [12 - len(id_list) if len(id_list) < 12 else 1])
                
                for idx, target_id in enumerate(id_list):
                    target_row = df_data[df_data['ID'] == target_id]
                    if not target_row.empty:
                        target_data = target_row.iloc[0]
                        with cols_vazby[idx]:
                            if st.button(f"🔗 {target_data['Zkratka']}", key=f"vazba_btn_{st.session_state.zvolena_zkratka}_{target_id}", help=target_data['Ukazatel']):
                                prejit_na_ukazatel(target_data['Zkratka'])
                                st.rerun()
            else:
                st.text(f"🔗 Kontext: {vazby_raw}")

        # Sekce 5: Interaktivní kalkulačka (dole)
        st.markdown("---")
        with st.expander(f"🧮 Spustit pomocnou kalkulačku pro {row['Zkratka']}", expanded=False):
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

    # SCÉNÁŘ 2: HLAVNÍ ROZCESTNÍK
    else:
        row1_col1, row1_col2, row1_col3 = st.columns(3)
        row2_col1, row2_col2, row2_col3 = st.columns(3)

        mrizka_sjednocena = [
            {"panel": row1_col1, "panel_id": "Výsledovka", "db_kategorie": ["Výsledovka"]},
            {"panel": row1_col2, "panel_id": "Rozvaha", "db_kategorie": ["Rozvaha"]},
            {"panel": row1_col3, "panel_id": "Finanční zdraví", "db_kategorie": ["Finanční zdraví", "Rentabilita", "Likvidita", "Zadluženost"]},
            {"panel": row2_col1, "panel_id": "Valuace", "db_kategorie": ["Valuace", "Kombinované", "Tržní ocenění"]},
            {"panel": row2_col2, "panel_id": "Makroekonomie", "db_kategorie": ["Makroekonomie", "Makro"]},
            {"panel": row2_col3, "panel_id": "Makro / Sentiment", "db_kategorie": ["Makro / Sentiment", "Sentiment"]}
        ]

        for radek in mrizka_sjednocena:
            with radek["panel"]:
                with st.container(border=True):
                    st.markdown(f"### 📂 {radek['panel_id']}")
                    
                    kat_info = df_kat[df_kat["Nazev_Kategorie"] == radek["panel_id"]]
                    if not kat_info.empty:
                        st.write(kat_info["Uvodni_Text"].iloc[0][:130] + "...")
                    
                    st.write("**Hlavní ukazatele:**")
                    
                    sloupec_hlavni = [c for c in df_data.columns if c.lower().replace(" ", "") == "hlavni_ukazatel"]
                    hlavni_ukazatele = pd.DataFrame()
                    if sloupec_hlavni:
                        real_col = sloupec_hlavni[0]
                        hlavni_ukazatele = df_data[
                            (df_data["Kategorie"].isin(radek["db_kategorie"])) & 
                            (df_data[real_col].astype(str).str.strip().str.upper() == "ANO")
                        ]
                    
                    if not hlavni_ukazatele.empty and len(hlavni_ukazatele) > 0:
                        cols_buttons = st.columns(len(hlavni_ukazatele))
                        for idx, (_, u_row) in enumerate(hlavni_ukazatele.iterrows()):
                            with cols_buttons[idx]:
                                if st.button(u_row["Zkratka"], key=f"grid_btn_{radek['panel_id']}_{u_row['Zkratka']}", help=u_row["Ukazatel"]):
                                    prejit_na_ukazatel(u_row["Zkratka"])
                                    st.rerun()
                    else:
                        st.caption("Žádné zkratky nebyly označeny jako hlavní.")
                    
                    with st.expander("Zobrazit celou kategorii", expanded=False):
                        if not kat_info.empty:
                            st.write(kat_info["Uvodni_Text"].iloc[0])
                            if "Co_Zde_Najdete" in df_kat.columns:
                                st.markdown(f"**Co zde najdete:** {kat_info['Co_Zde_Najdete'].iloc[0]}")
                        
                        st.write("**Všechny položky této kategorie:**")
                        vsechny_kat_polozky = df_data[df_data["Kategorie"].isin(radek["db_kategorie"])].sort_values(by="Zkratka")
                        
                        for _, p_row in vsechny_kat_polozky.iterrows():
                            if st.button(f"🔍 {p_row['Zkratka']} - {p_row['Ukazatel']}", key=f"exp_list_{radek['panel_id']}_{p_row['Zkratka']}"):
                                prejit_na_ukazatel(p_row["Zkratka"])
                                st.rerun()
else:
    st.info("Zkontrolujte nastavení listů ve vaší Google Tabulce.")
