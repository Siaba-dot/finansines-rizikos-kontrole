# app.py – Klaidų analizė su automatine finansine rizika ir HH:MM:SS laikais
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Klaidų analizė", layout="wide")
st.title("📊 Klaidų analizė ir procesų tobulinimas")

# ----------------------------
# 1. DUOMENŲ ĮKĖLIMAS
# ----------------------------
uploaded_file = st.file_uploader("Įkelkite Excel klaidų registrą", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # ----------------------------
    # 2. KLAIDOS IDENTIFIKACIJA
    # ----------------------------
    df["Yra klaida"] = df["Klaidos tipas"].notna() & (df["Klaidos tipas"].astype(str).str.strip() != "")
    klaidos_df = df[df["Yra klaida"]].copy()

    # ----------------------------
    # 3. FINANSINĖ RIZIKA – AUTOMATIZUOTA
    # ----------------------------
    def nustatyti_finansine_rizika(row):
        try:
            suma = float(row.get("Suma EUR, be PVM", 0))
        except:
            suma = 0

        klaidos_tipas = str(row.get("Klaidos tipas", "")).lower()

        # Tikriname, ar klaidos tipuose yra "terminas"
        if "terminas" in klaidos_tipas:
            return suma
        else:
            return 0

    klaidos_df["Finansinė rizika (€)"] = klaidos_df.apply(nustatyti_finansine_rizika, axis=1)

    # ----------------------------
    # 4. TAISYMO LAIKO SKAIČIAVIMAS (HH:MM:SS)
    # ----------------------------
    klaidos_df["Pradžia"] = pd.to_datetime(
        klaidos_df["Klaidos ištaisymo laiko pradžia"], format="%H:%M:%S", errors="coerce"
    )
    klaidos_df["Pabaiga"] = pd.to_datetime(
        klaidos_df["Klaidos ištaisymo laiko pabaiga"], format="%H:%M:%S", errors="coerce"
    )

    # Taisymo laikas minutėmis
    klaidos_df["Taisymo laikas (min)"] = (
        (klaidos_df["Pabaiga"] - klaidos_df["Pradžia"]).dt.total_seconds() / 60
    )

    # Jei pabaiga < pradžia (per naktį), pridėti 24h
    klaidos_df["Taisymo laikas (min)"] = klaidos_df["Taisymo laikas (min)"].apply(
        lambda x: x + 24*60 if x < 0 else x
    )

    klaidos_df["Taisymo laikas (val)"] = klaidos_df["Taisymo laikas (min)"] / 60

    # ----------------------------
    # 5. KLAIDOS SUNKUMO NUSTATYMAS
    # ----------------------------
    def nustatyti_sunkuma(row):
        rizika = row.get("Finansinė rizika (€)", 0)
        laikas = row.get("Taisymo laikas (min)", 0)

        if rizika >= 1000 or laikas >= 240:
            return "Kritinė"
        elif rizika >= 100 or laikas >= 60:
            return "Vidutinė"
        elif rizika > 0:
            return "Maža"
        else:
            return "Administracinė"

    klaidos_df["Klaidos sunkumas"] = klaidos_df.apply(nustatyti_sunkuma, axis=1)

    # ----------------------------
    # 6. KPI – vadovų „WOW“
    # ----------------------------
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📌 Tikrų klaidų skaičius", len(klaidos_df))
    col2.metric("⏱️ Prarastas laikas (val)", round(klaidos_df["Taisymo laikas (val)"].sum(), 2))
    col3.metric("💰 Bendra finansinė rizika (€)", round(klaidos_df["Finansinė rizika (€)"].sum(), 2))
    col4.metric("🔥 Kritinių klaidų", (klaidos_df["Klaidos sunkumas"] == "Kritinė").sum())

    # ----------------------------
    # 7. ANALIZĖ
    # ----------------------------
    st.subheader("📈 Klaidų pasiskirstymas pagal sunkumą")
    fig1 = px.bar(
        klaidos_df.groupby("Klaidos sunkumas").size().reset_index(name="Kiekis"),
        x="Klaidos sunkumas",
        y="Kiekis",
        color="Klaidos sunkumas"
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("🏭 Klaidos pagal proceso etapą")
    fig2 = px.bar(
        klaidos_df.groupby("Proceso etapas").size().reset_index(name="Kiekis"),
        x="Proceso etapas",
        y="Kiekis"
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("👥 Atsakomybės pasiskirstymas")
    fig3 = px.pie(
        klaidos_df,
        names="Atsakinga puse",
        title="Kas realiai generuoja klaidas"
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ----------------------------
    # 8. GRAFINIS TAISYMO LAIKO VAIZDAVIMAS
    # ----------------------------
    st.subheader("⏱️ Klaidų taisymo laikas (val)")
    fig4 = px.bar(
        klaidos_df,
        x="Klaidos tipas",
        y="Taisymo laikas (val)",
        color="Klaidos sunkumas",
        hover_data=["Finansinė rizika (€)", "Proceso etapas", "Atsakinga puse"],
        title="Kiekvienos klaidos taisymo laikas"
    )
    st.plotly_chart(fig4, use_container_width=True)

    # ----------------------------
    # 9. TOP 5 SKAUSMO TAŠKAI
    # ----------------------------
    st.subheader("🚨 TOP 5 didžiausios klaidos")
    top5 = klaidos_df.sort_values(
        by=["Finansinė rizika (€)", "Taisymo laikas (min)"],
        ascending=False
    ).head(5)
    st.dataframe(top5)

    # ----------------------------
    # 10. VADOVŲ SANTRAUKA
    # ----------------------------
    st.subheader("🎯 Vadovų santrauka")
    st.markdown(f"""
    * Užregistruota **{len(df)} įrašų**, tačiau **tik {len(klaidos_df)} yra realios klaidos**.
    * Per laikotarpį prarasta **{round(klaidos_df['Taisymo laikas (val)'].sum(),2)} val. darbo laiko**.
    * Didžiausia rizika kyla **{klaidos_df.groupby('Proceso etapas').size().idxmax()}** etape.
    * Problema yra **procesinė**, ne pavieniai darbuotojai.
    """)

else:
    st.info("Įkelkite Excel failą, kad pradėtume analizę")
