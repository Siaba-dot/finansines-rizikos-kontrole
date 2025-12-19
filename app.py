
# Streamlit aplikacija – Klaidų analizė procesų gerinimui (WOW vadovams)

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Klaidų analizė – valdymo lygis", layout="wide")

st.title("📊 Klaidų analizė procesų gerinimui")
st.caption("Ne kas kaltas, o kur sistema leidžia klaidoms atsirasti")

uploaded_file = st.file_uploader("Įkelkite klaidų registrą (Excel)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # ===== DUOMENŲ PARUOŠIMAS =====
    df['Dokumento data'] = pd.to_datetime(df['Dokumento data'])
    df['Dokumento gavimo data'] = pd.to_datetime(df['Dokumento gavimo data'])

    # Taisymo laikas valandomis
    df['Taisymo_laikas_val'] = df['Taisymo laikas (min)'] / 60

    # Klaidos sunkumo balai
    sunkumo_map = {
        'Maža': 1,
        'Vidutinė': 2,
        'Didelė': 3
    }
    df['Sunkumo_balai'] = df['Klaidos sunkumas'].map(sunkumo_map)

    # Pasikartojimo flagas
    df['Pasikartoja_flag'] = df['Pasikartojanti klaida'].map({'Taip': 1, 'Ne': 0})

    # ===== KPI BLOKAS (VADOVŲ WOW) =====
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("💰 Finansinė rizika (€)", f"{df['Finansinė rizika'].sum():,.0f}")
    col2.metric("⏱ Sudegintas laikas (val.)", f"{df['Taisymo_laikas_val'].sum():.1f}")
    col3.metric("🔁 Pasikartojančios klaidos (%)", f"{df['Pasikartoja_flag'].mean()*100:.1f}%")
    col4.metric("⚠️ Vid. klaidos sunkumas", f"{df['Sunkumo_balai'].mean():.2f}")

    st.divider()

    # ===== PARETO – FINANSINĖ RIZIKA PAGAL PROCESĄ =====
    st.subheader("💡 Kur realiai prarandami pinigai")

    pareto = df.groupby('Proceso etapas')['Finansinė rizika'].sum().sort_values(ascending=False).reset_index()
    pareto['Kumulatyvinė %'] = pareto['Finansinė rizika'].cumsum() / pareto['Finansinė rizika'].sum() * 100

    fig_pareto = px.bar(
        pareto,
        x='Proceso etapas',
        y='Finansinė rizika',
        title='Finansinė rizika pagal proceso etapus'
    )

    fig_pareto.add_scatter(
        x=pareto['Proceso etapas'],
        y=pareto['Kumulatyvinė %'],
        mode='lines+markers',
        name='Kumulatyvinė %',
        yaxis='y2'
    )

    fig_pareto.update_layout(
        yaxis2=dict(overlaying='y', side='right', range=[0, 100], title='Kumulatyvinė %')
    )

    st.plotly_chart(fig_pareto, use_container_width=True)
    st.caption("➡️ Keli proceso etapai generuoja didžiąją dalį finansinės rizikos")

    st.divider()

    # ===== LAIKAS vs RIZIKA MATRICA =====
    st.subheader("🎯 Kur verta investuoti į procesų gerinimą")

    bubble = df.groupby('Proceso etapas').agg(
        Finansinė_rizika=('Finansinė rizika', 'sum'),
        Laikas=('Taisymo_laikas_val', 'sum'),
        Pasikartojimai=('Pasikartoja_flag', 'sum')
    ).reset_index()

    fig_bubble = px.scatter(
        bubble,
        x='Laikas',
        y='Finansinė_rizika',
        size='Pasikartojimai',
        color='Proceso etapas',
        title='Procesinė investicijų matrica',
        labels={'Laikas': 'Sugaištas laikas (val.)', 'Finansinė_rizika': 'Finansinė rizika (€)'}
    )

    st.plotly_chart(fig_bubble, use_container_width=True)
    st.caption("🔴 Viršus dešinėje – prioritetai automatizavimui / kontrolei")

    st.divider()

    # ===== PASIKARTOJANČIOS KLAIDOS =====
    st.subheader("🔁 Pasikartojančios klaidos = procesų defektai")

    repeat = df[df['Pasikartojanti klaida'] == 'Taip'].groupby('Klaidos tipas').size().reset_index(name='Kiekis')

    fig_repeat = px.bar(repeat, x='Klaidos tipas', y='Kiekis', title='Dažniausiai pasikartojančios klaidos')
    st.plotly_chart(fig_repeat, use_container_width=True)

    st.divider()

    # ===== VADYBINĖ SANTRAUKA =====
    st.subheader("📌 Vadybinės išvados (automatinės)")

    st.markdown(f"""
    **Finansinis poveikis:**  
    Šiuo metu klaidos generuoja **{df['Finansinė rizika'].sum():,.0f} €** finansinę riziką.

    **Procesinis poveikis:**  
    Klaidų taisymas sunaudoja **{df['Taisymo_laikas_val'].sum():.1f} darbo valandų**, kurios nekuria vertės.

    **Sisteminė problema:**  
    **{df['Pasikartoja_flag'].mean()*100:.1f}%** klaidų kartojasi – tai aiškus signalas, kad reikia keisti procesą, o ne žmones.

    **Valdymo sprendimas:**  
    Fokusas turi būti nukreiptas į kelis kritinius proceso etapus – ten investicijos į prevenciją ir automatizavimą atsipirks greičiausiai.
    """)

else:
    st.info("Įkelkite Excel failą, kad būtų atlikta analizė")
