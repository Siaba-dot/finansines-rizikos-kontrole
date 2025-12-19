import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# =====================================
# STREAMLIT KONFIGŪRACIJA
# =====================================
st.set_page_config(
    page_title="Klaidų analizė – valdymo lygis",
    layout="wide"
)

st.title("📊 Klaidų analizė procesų gerinimui")
st.caption("Ne kas kaltas, o kur sistema leidžia klaidoms atsirasti")

uploaded_file = st.file_uploader(
    "📂 Įkelkite klaidų registrą (Excel)",
    type=["xlsx"]
)

if uploaded_file:

    # =====================================
    # DUOMENŲ NUSKAITYMAS
    # =====================================
    df = pd.read_excel(uploaded_file)

    st.success(f"Įkelta įrašų: {len(df)}")

    # =====================================
    # DATŲ TVARKYMAS (NEPRIVALOMA, BET SAUGU)
    # =====================================
    for col in ["Dokumento data", "Dokumento gavimo data"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # =====================================
    # TAISYMO LAIKO IŠVALYMAS (KRITINĖ VIETA)
    # =====================================
    if "Taisymo laikas (min)" in df.columns:
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

        df["Taisymo_laikas_val"] = df["Taisymo laikas (min)"] / 60
    else:
        st.error("❌ Nėra stulpelio 'Taisymo laikas (min)'")
        st.stop()

    # =====================================
    # KLAIDOS SUNKUMO BALAI
    # =====================================
    if "Klaidos sunkumas" in df.columns:
        sunkumo_map = {
            "Maža": 1,
            "Vidutinė": 2,
            "Didelė": 3
        }
        df["Sunkumo_balai"] = df["Klaidos sunkumas"].map(sunkumo_map)
    else:
        df["Sunkumo_balai"] = np.nan

    # =====================================
    # PASIKARTOJIMO FLAGAS
    # =====================================
    if "Pasikartojanti klaida" in df.columns:
        df["Pasikartoja_flag"] = df["Pasikartojanti klaida"].map(
            {"Taip": 1, "Ne": 0}
        )
    else:
        df["Pasikartoja_flag"] = 0

    # =====================================
    # FINANSINĖ RIZIKA
    # =====================================
    if "Finansinė rizika" in df.columns:
        df["Finansinė rizika"] = pd.to_numeric(
            df["Finansinė rizika"],
            errors="coerce"
        )
    else:
        st.error("❌ Nėra stulpelio 'Finansinė rizika'")
        st.stop()

    # =====================================
    # KPI BLOKAS – WOW VADOVAMS
    # =====================================
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "💰 Finansinė rizika (€)",
        f"{df['Finansinė rizika'].sum():,.0f}"
    )

    col2.metric(
        "⏱ Sudegintas laikas (val.)",
        f"{df['Taisymo_laikas_val'].sum():.1f}"
    )

    col3.metric(
        "🔁 Pasikartojančios klaidos (%)",
        f"{df['Pasikartoja_flag'].mean() * 100:.1f}%"
    )

    col4.metric(
        "⚠️ Vid. klaidos sunkumas",
        f"{df['Sunkumo_balai'].mean():.2f}"
    )

    # =====================================
    # DUOMENŲ KOKYBĖ (BRANDOS SIGNALAS)
    # =====================================
    invalid_time = df["Taisymo laikas (min)"].isna().sum()

    if invalid_time > 0:
        st.warning(
            f"⚠️ {invalid_time} įrašų neturi korektiško taisymo laiko. "
            "Tai duomenų kokybės, o ne darbuotojų problema."
        )

    st.divider()

    # =====================================
    # PARETO – FINANSINĖ RIZIKA PAGAL PROCESĄ
    # =====================================
    if "Proceso etapas" in df.columns:
        st.subheader("💡 Kur realiai prarandami pinigai")

        pareto = (
            df.groupby("Proceso etapas")["Finansinė rizika"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )

        pareto["Kumulatyvinė %"] = (
            pareto["Finansinė rizika"].cumsum()
            / pareto["Finansinė rizika"].sum()
            * 100
        )

        fig_pareto = px.bar(
            pareto,
            x="Proceso etapas",
            y="Finansinė rizika",
            title="Finansinė rizika pagal proceso etapus"
        )

        fig_pareto.add_scatter(
            x=pareto["Proceso etapas"],
            y=pareto["Kumulatyvinė %"],
            mode="lines+markers",
            name="Kumulatyvinė %",
            yaxis="y2"
        )

        fig_pareto.update_layout(
            yaxis2=dict(
                overlaying="y",
                side="right",
                range=[0, 100],
                title="Kumulatyvinė %"
            )
        )

        st.plotly_chart(fig_pareto, use_container_width=True)

    st.divider()

    # =====================================
    # LAIKAS vs RIZIKA – INVESTICIJŲ MATRICA
    # =====================================
    st.subheader("🎯 Kur verta investuoti į procesų gerinimą")

    bubble = df.groupby("Proceso etapas").agg(
        Finansinė_rizika=("Finansinė rizika", "sum"),
        Laikas=("Taisymo_laikas_val", "sum"),
        Pasikartojimai=("Pasikartoja_flag", "sum")
    ).reset_index()

    fig_bubble = px.scatter(
        bubble,
        x="Laikas",
        y="Finansinė_rizika",
        size="Pasikartojimai",
        color="Proceso etapas",
        title="Procesinė investicijų matrica",
        labels={
            "Laikas": "Sugaištas laikas (val.)",
            "Finansinė_rizika": "Finansinė rizika (€)"
        }
    )

    st.plotly_chart(fig_bubble, use_container_width=True)

    st.divider()

    # =====================================
    # PASIKARTOJANČIOS KLAIDOS
    # =====================================
    if "Klaidos tipas" in df.columns:
        st.subheader("🔁 Pasikartojančios klaidos = procesų defektai")

        repeat = (
            df[df["Pasikartoja_flag"] == 1]
            .groupby("Klaidos tipas")
            .size()
            .reset_index(name="Kiekis")
            .sort_values("Kiekis", ascending=False)
        )

        fig_repeat = px.bar(
            repeat,
            x="Klaidos tipas",
            y="Kiekis",
            title="Dažniausiai pasikartojančios klaidos"
        )

        st.plotly_chart(fig_repeat, use_container_width=True)

    st.divider()

    # =====================================
    # AUTOMATINĖ VADYBINĖ IŠVADA
    # =====================================
    st.subheader("📌 Vadybinės išvados")

    st.markdown(f"""
    **Finansinis poveikis**  
    Įmonė šiuo metu realiai „finansuoja“ klaidas už **{df['Finansinė rizika'].sum():,.0f} €**.

    **Procesinis poveikis**  
    Klaidų taisymas sunaudoja **{df['Taisymo_laikas_val'].sum():.1f} darbo valandų**, kurios nekuria vertės.

    **Sisteminė problema**  
    **{df['Pasikartoja_flag'].mean() * 100:.1f}%** klaidų kartojasi – tai procesų, o ne žmonių problema.

    **Valdymo sprendimas**  
    Fokusas turi būti nukreiptas į kelis kritinius proceso etapus – ten automatizacija ir prevencija atsipirks greičiausiai.
    """)

else:
    st.info("👆 Įkelkite Excel failą, kad būtų atlikta analizė")
