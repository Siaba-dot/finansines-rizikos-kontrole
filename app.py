import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# =====================================
# KONFIGŪRACIJA
# =====================================
st.set_page_config(page_title="Klaidų analizė – valdymo lygis", layout="wide")

st.title("📊 Klaidų analizė procesų gerinimui")
st.caption("Skaičiuojama realybė, ne gražūs nuliai")

uploaded_file = st.file_uploader(
    "📂 Įkelkite klaidų registrą (Excel)",
    type=["xlsx"]
)

# =====================================
# KONSTANTOS (VALDYMO SPRENDIMAS)
# =====================================
DEFAULT_TAISYMO_MIN = 15       # jei nenurodyta – minimalus realus laikas
DEFAULT_SUNKUMAS = 2           # vidutinė klaida
VALANDOS_KAINA = 25            # € / val. (galima keisti)

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.success(f"Įkelta įrašų: {len(df)}")

    # =====================================
    # 1. KLAIDOS FAKTAS
    # =====================================
    df["Yra_klaida"] = 1   # jei įrašas registre – klaida egzistuoja

    # =====================================
    # 2. DATOS
    # =====================================
    for col in [
        "Dokumento data",
        "Dokumento gavimo data",
        "Klaidos ištaisymo laiko pradžia",
        "Klaidos ištaisymo laiko pabaiga"
    ]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # =====================================
    # 3. TAISYMO LAIKAS (VISADA BUS)
    # =====================================
    df["Taisymo laikas (min)"] = (
        df["Taisymo laikas (min)"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.extract(r"(\d+\.?\d*)")[0]
    )

    df["Taisymo laikas (min)"] = pd.to_numeric(
        df["Taisymo laikas (min)"],
        errors="coerce"
    )

    # jei nenurodyta – priskiriam standartą
    df["Taisymo laikas (min)"] = df["Taisymo laikas (min)"].fillna(DEFAULT_TAISYMO_MIN)
    df["Taisymo_laikas_val"] = df["Taisymo laikas (min)"] / 60

    # =====================================
    # 4. KLAIDOS SUNKUMAS (NORMALIZUOTAS)
    # =====================================
    df["Klaidos sunkumas"] = (
        df["Klaidos sunkumas"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    sunkumo_map = {
        "maža": 1,
        "vidutinė": 2,
        "didelė": 3
    }

    df["Sunkumo_balai"] = df["Klaidos sunkumas"].map(sunkumo_map)
    df["Sunkumo_balai"] = df["Sunkumo_balai"].fillna(DEFAULT_SUNKUMAS)

    # =====================================
    # 5. PASIKARTOJIMAS
    # =====================================
    df["Pasikartoja_flag"] = (
        df["Pasikartojanti klaida"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({"taip": 1, "ne": 0})
        .fillna(0)
    )

    # =====================================
    # 6. FINANSINĖ RIZIKA
    # =====================================
    df["Finansinė rizika"] = pd.to_numeric(
        df["Finansinė rizika"],
        errors="coerce"
    ).fillna(0)

    # =====================================
    # 7. DARBO KAŠTAI (WOW FAKTORIUS)
    # =====================================
    df["Darbo_kaina_EUR"] = df["Taisymo_laikas_val"] * VALANDOS_KAINA

    # =====================================
    # KPI BLOKAS
    # =====================================
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("📌 Klaidų skaičius", int(df["Yra_klaida"].sum()))
    col2.metric("⏱ Taisymo laikas (val.)", f"{df['Taisymo_laikas_val'].sum():.1f}")
    col3.metric("💰 Finansinė rizika (€)", f"{df['Finansinė rizika'].sum():,.0f}")
    col4.metric("💸 Darbo kaštai (€)", f"{df['Darbo_kaina_EUR'].sum():,.0f}")
    col5.metric("⚠️ Vid. sunkumas", f"{df['Sunkumo_balai'].mean():.2f}")

    # =====================================
    # DUOMENŲ KOKYBĖS SIGNALAI
    # =====================================
    neivertintas_laikas = (df["Taisymo laikas (min)"] == DEFAULT_TAISYMO_MIN).sum()
    neivertintas_sunkumas = (df["Klaidos sunkumas"] == "nan").sum()

    if neivertintas_laikas > 0:
        st.warning(
            f"⚠️ {neivertintas_laikas} klaidų neturėjo taisymo laiko – "
            "panaudotas standartinis 15 min."
        )

    if neivertintas_sunkumas > 0:
        st.warning(
            f"⚠️ {neivertintas_sunkumas} klaidų neturėjo nurodyto sunkumo – "
            "laikytos vidutinėmis."
        )

    st.divider()

    # =====================================
    # PARETO – PROCESO ETAPAI
    # =====================================
    st.subheader("💡 Kur procesas labiausiai brokuotas")

    pareto = (
        df.groupby("Proceso etapas")
        .agg(
            Rizika=("Finansinė rizika", "sum"),
            Laikas=("Taisymo_laikas_val", "sum"),
            Kiekis=("Yra_klaida", "sum")
        )
        .sort_values("Rizika", ascending=False)
        .reset_index()
    )

    fig = px.bar(
        pareto,
        x="Proceso etapas",
        y="Rizika",
        title="Finansinė rizika pagal proceso etapus"
    )

    st.plotly_chart(fig, use_container_width=True)

    # =====================================
    # INVESTICIJŲ MATRICA
    # =====================================
    st.subheader("🎯 Kur verta investuoti")

    fig2 = px.scatter(
        pareto,
        x="Laikas",
        y="Rizika",
        size="Kiekis",
        color="Proceso etapas",
        labels={
            "Laikas": "Sugaištas laikas (val.)",
            "Rizika": "Finansinė rizika (€)"
        }
    )

    st.plotly_chart(fig2, use_container_width=True)

    # =====================================
    # AUTOMATINĖ IŠVADA
    # =====================================
    st.subheader("📌 Vadybinė išvada")

    st.markdown(f"""
    - Užregistruota **{int(df['Yra_klaida'].sum())} klaidų**
    - Klaidų taisymas sunaudojo **{df['Taisymo_laikas_val'].sum():.1f} val.**
    - Tiesioginė finansinė rizika: **{df['Finansinė rizika'].sum():,.0f} €**
    - Vidutinis klaidos sunkumas: **{df['Sunkumo_balai'].mean():.2f}**
    - Reikalingas procesų stiprinimas keliuose kritiniuose etapuose
    """)

else:
    st.info("👆 Įkelkite Excel failą, kad būtų atlikta analizė")
