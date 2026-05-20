import streamlit as st
import pandas as pd

# Nastavení stránky (široké rozložení)
st.set_page_config(page_title="Průvodce Akciovými Ukazateli", layout="wide", page_icon="📊")

# URL vaší Google Tabulky
spreadsheet_url = "https://docs.google.com/spreadsheets/d/12KhfbhPQtJnlj_987Lo8CT7dUJ0GYSexu7tOunaGLdw/edit?gid=96365177#gid=96365177"

# Úprava URL pro export do CSV
if "edit?usp=sharing" in spreadsheet_url:
    csv_url = spreadsheet_url.replace("edit?usp=sharing", "export?format=csv")
elif "edit#" in spreadsheet_url:
    csv_url = spreadsheet_url.split("edit#")[0] + "export?format=csv"
elif "edit?" in spreadsheet_url:
    csv_url = spreadsheet_url.split("edit?")[0] + "export?format=csv"
else:
    csv_url = spreadsheet_url.rstrip("/") + "/export?format=csv"

# Načtení dat s kešováním
@st.cache_data
def load_data(url):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        # Ujistíme se, že ID je bráno jako celé číslo a vyčistíme případné textové sloupce
        if 'ID' in df.columns:
            df['ID'] = pd.to_numeric(df['ID'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Nepodařilo se načíst data z Google Tabulky. Chyba: {e}")
        return None

df = load_data(csv_url)

# Společný nadpis
st.title("📊 Průvodce Akciovými Ukazateli")
st.write("Interaktivní manuál pro interpretaci fundamentálních a makroekonomických veličin.")

if df is not None:
    # --- SIDEBAR: FILTRACE A VÝBĚR ---
    kategorie_list = ["Všechny"] + list(df["Kategorie"].dropna().unique())
    zvolena_kategorie = st.sidebar.selectbox("Vyberte kategorii:", kategorie_list)

    if zvolena_kategorie != "Všechny":
        filtr_df = df[df["Kategorie"] == zvolena_kategorie]
    else:
        filtr_df = df

    # Řazení seznamu ukazatelů podle abecedy pro snazší hledání v aplikaci
    filtr_df = filtr_df.sort_values(by="Zkratka")
    ukazatel_list = list(filtr_df["Zkratka"].dropna().unique())
    zvoleny_ukazatel = st.sidebar.selectbox("Vyberte konkrétní položku:", ukazatel_list)

    # Načtení konkrétního řádku dat
    row = filtr_df[filtr_df["Zkratka"] == zvoleny_ukazatel].iloc[0]
    current_id = row['ID']

    # --- HLAVNÍ PLOCHA: DETAIL UKAZATELE ---
    st.header(f"{row['Ukazatel']} ({row['Zkratka']})")
    st.caption(f"Kategorie: {row['Kategorie']} | ID kód v databázi: {int(current_id) if pd.notnull(current_id) else 'N/A'}")
    st.markdown("---")

    # 1. SEKCE: VZOREC
    st.subheader("🧮 Vzorec / Konstrukce")
    st.info(f"**{row['Vzorec']}**")

    # 2. SEKCE: CHARAKTERISTIKA A INTERPRETACE
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 💡 Co představuje?")
        st.write(row["Hlavni_Charakteristika"])
    with col2:
        st.markdown("### 🔍 Jak ho číst a interpretovat?")
        st.write(row["Jak_Interpretovat"])

    st.markdown("---")

    # 3. SEKCE: POSOUZENÍ HODNOT
    st.subheader("📈 Vodítko k posouzení hodnot")
    col3, col4 = st.columns(2)
    with col3:
        st.success(f"**Optimální / Obvyklé hodnoty:**\n\n{row['Optimalni_Hodnoty']}")
    with col4:
        st.error(f"**Kritické / Rizikové hodnoty:**\n\n{row['Kriticke_Hodnoty']}")

    st.markdown("---")

    # 4. SEKCE: DYNAMICKÁ FINANČNÍ KALKULAČKA
    st.subheader("🧮 Interaktivní kalkulačka")
    with st.expander(f"Otevřít kalkulačku pro: {row['Zkratka']}", expanded=False):
        # Ukázka plně funkční kalkulačky pro P/E
        if row['Zkratka'] == 'P/E':
            st.write("Spočítejte si aktuální P/E násobek vybrané akcie:")
            calc_price = st.number_input("Aktuální cena akcie (např. v USD nebo CZK):", min_value=0.0, value=150.0, step=1.0)
            calc_eps = st.number_input("Zisk na akcii (EPS):", min_value=0.01, value=7.5, step=0.1)
            result_pe = calc_price / calc_eps
            st.metric(label="Výsledné P/E", value=f"{result_pe:.2f}")
            if result_pe > 30:
                st.warning("⚠️ Hodnota P/E je vysoká. Trh od této firmy očekává masivní budoucí růst.")
            elif result_pe < 10:
                st.info("ℹ️ Hodnota P/E je nízká. Může jít o podhodnocenou akcii, nebo o firmu v potížích (hodnotová past).")
            else:
                st.success("✅ Hodnota P/E se pohybuje v běžném historickém průměru.")

        # Ukázka plně funkční kalkulačky pro Net Margin
        elif row['Zkratka'] == 'Net Margin':
            st.write("Spočítejte si čistou ziskovou marži podniku:")
            calc_profit = st.number_input("Čistý zisk po zdanění (EAT):", min_value=0.0, value=150000.0, step=1000.0)
            calc_sales = st.number_input("Celkové tržby (Sales):", min_value=1.0, value=1000000.0, step=1000.0)
            result_margin = (calc_profit / calc_sales) * 100
            st.metric(label="Čistá marže", value=f"{result_margin:.2f} %")
            if result_margin > 15:
                st.success("✅ Skvělá marže! Firma má pravděpodobně silnou konkurenční výhodu.")
            elif result_margin < 5:
                st.error("⚠️ Nízká marže. Byznys je vysoce zranitelný vůči růstu nákladů.")

        # Univerzální šablona pro ostatní ukazatele
        else:
            st.write(f"Pro ukazatel **{row['Zkratka']}** se kalkulačka připravuje. Vstupní hodnoty budou odpovídat vzorci: `{row['Vzorec']}`.")
            st.text_input("Vstupní hodnota A:", placeholder="Zatím neaktivní")
            st.text_input("Vstupní hodnota B:", placeholder="Zatím neaktivní")

    st.markdown("---")

    # 5. SEKCE: CHYTRÉ VAZBY NA JINÁ ID
    st.subheader("🔗 Vazby na jiné ukazatele a kontext")
    vazby_raw = str(row["Vazby_Na_Jine_Ukazatele"]).strip()

    if vazby_raw and vazby_raw != "nan" and vazby_raw != "":
        st.write("Tato položka úzce souvisí s následujícími pojmy v našem manuálu:")
        
        # Zkusíme rozparsovat ID čísla oddělená čárkou
        try:
            # Převedeme text "41, 6" na seznam čísel [41, 6]
            id_list = [int(x.strip()) for x in vazby_raw.split(",") if x.strip().isdigit()]
            
            if id_list:
                for target_id in id_list:
                    # Najdeme v našem hlavním DataFrame řádek, který má toto ID
                    target_row = df[df['ID'] == target_id]
                    if not target_row.empty:
                        target_data = target_row.iloc[0]
                        # Vypíšeme klikatelnou informaci (uživatel si může název najít v sidebaru)
                        st.markdown(f"* **{target_data['Zkratka']}** – {target_data['Ukazatel']} *(Kategorie: {target_data['Kategorie']})*")
            else:
                # Pokud v poli není seznam čísel, ale původní text, vypíšeme ho normálně
                st.warning(vazby_raw)
        except Exception:
            # Záložní řešení, pokud by parsování selhalo
            st.warning(vazby_raw)
    else:
        st.info("Pro tento ukazatel zatím nebyly definovány žádné specifické číselné vazby.")

else:
    st.info("Zkontrolujte, zda je vaše Google Tabulka správně načtená a veřejně dostupná pro čtení.")
