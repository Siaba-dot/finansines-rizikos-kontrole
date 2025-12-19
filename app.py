# app.py – Klaidų analizė su slide-like HTML ataskaita ir spalvomis
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
import io

st.set_page_config(page_title="Klaidų analizė", layout="wide")
st.title("📊 Klaidų analizė su slide-like HTML ataskaita ir spalvomis")

uploaded_file = st.file_uploader("Įkelkite Excel klaidų registrą", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # ----------------------------
    # 1. Klaidos identifikacija
    # ----------------------------
    df["Yra klaida"] = df["Klaidos tipas"].notna() & (df["Klaidos tipas"].astype(str).str.strip() != "")
    klaidos_df = df[df["Yra klaida"]].copy()

    # ----------------------------
    # 2. Finansinė rizika
    # ----------------------------
    def nustatyti_finansine_rizika(row):
        try:
            suma = float(row.get("Suma EUR, be PVM", 0))
        except:
            suma = 0
        klaidos_tipas = str(row.get("Klaidos tipas", "")).lower()
        if "terminas" in klaidos_tipas:
            return suma
        else:
            return 0

    klaidos_df["Finansinė rizika (€)"] = klaidos_df.apply(nustatyti_finansine_rizika, axis=1)

    # ----------------------------
    # 3. Taisymo laikas HH:MM:SS
    # ----------------------------
    klaidos_df["Pradžia"] = pd.to_datetime(
        klaidos_df["Klaidos ištaisymo laiko pradžia"], format="%H:%M:%S", errors="coerce"
    )
    klaidos_df["Pabaiga"] = pd.to_datetime(
        klaidos_df["Klaidos ištaisymo laiko pabaiga"], format="%H:%M:%S", errors="coerce"
    )
    klaidos_df["Taisymo laikas (min)"] = (
        (klaidos_df["Pabaiga"] - klaidos_df["Pradžia"]).dt.total_seconds() / 60
    ).apply(lambda x: x + 24*60 if x < 0 else x)
    klaidos_df["Taisymo laikas (val)"] = klaidos_df["Taisymo laikas (min)"] / 60

    # ----------------------------
    # 4. Klaidos sunkumas
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

    # Spalvų žemėlapis grafikuose
    spalvos = {
        "Kritinė": "red",
        "Vidutinė": "orange",
        "Maža": "green",
        "Administracinė": "gray"
    }

    # ----------------------------
    # 5. KPI
    # ----------------------------
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📌 Tikrų klaidų skaičius", len(klaidos_df))
    col2.metric("⏱️ Prarastas laikas (val)", round(klaidos_df["Taisymo laikas (val)"].sum(), 2))
    col3.metric("💰 Bendra finansinė rizika (€)", round(klaidos_df["Finansinė rizika (€)"].sum(), 2))
    col4.metric("🔥 Kritinių klaidų", (klaidos_df["Klaidos sunkumas"] == "Kritinė").sum())

    # ----------------------------
    # 6. Grafikai su spalvomis pagal sunkumą
    # ----------------------------
    # Grafikas pagal sunkumą
    fig1 = px.bar(
        klaidos_df.groupby("Klaidos sunkumas").size().reset_index(name="Kiekis"),
        x="Klaidos sunkumas", y="Kiekis",
        color="Klaidos sunkumas",
        color_discrete_map=spalvos,
        title="Klaidų pasiskirstymas pagal sunkumą"
    )

    # Grafikas pagal proceso etapą + sunkumą
    etapas_sunkumas = klaidos_df.groupby(["Proceso etapas","Klaidos sunkumas"]).size().reset_index(name="Kiekis")
    fig2 = px.bar(
        etapas_sunkumas,
        x="Proceso etapas", y="Kiekis",
        color="Klaidos sunkumas",
        color_discrete_map=spalvos,
        title="Klaidos pagal proceso etapą ir sunkumą"
    )

    # Grafikas taisymo laikas pagal klaidos tipą
    fig3 = px.bar(
        klaidos_df,
        x="Klaidos tipas", y="Taisymo laikas (val)",
        color="Klaidos sunkumas",
        color_discrete_map=spalvos,
        hover_data=["Finansinė rizika (€)", "Proceso etapas", "Atsakinga puse"],
        title="Klaidų taisymo laikas (val)"
    )

    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig2, use_container_width=True)
    st.plotly_chart(fig3, use_container_width=True)

    # ----------------------------
    # 7. Slide-like HTML generavimas
    # ----------------------------
    if st.button("📤 Generuoti spalvotą slide-like HTML ataskaitą"):
        html_parts = []

        # Reveal.js + CSS
        reveal_head = """
        <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/reveal.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/theme/white.min.css">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/reveal.min.js"></script>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even){background-color: #f2f2f2;}
        .Kritinė {background-color: #F1948A;}
        .Vidutinė {background-color: #F9E79F;}
        .Maža {background-color: #ABEBC6;}
        .Administracinė {background-color: #D5DBDB;}
        h1, h2 {color: #2E86C1;}
        </style>
        </head>
        """
        html_parts.append("<html>" + reveal_head + "<body><div class='reveal'><div class='slides'>")

        # Slide 1 – KPI
        html_parts.append("<section><h1>KPI</h1>")
        html_parts.append(f"<p>Tikrų klaidų skaičius: {len(klaidos_df)}</p>")
        html_parts.append(f"<p>Prarastas laikas (val): {round(klaidos_df['Taisymo laikas (val)'].sum(),2)}</p>")
        html_parts.append(f"<p>Bendra finansinė rizika (€): {round(klaidos_df['Finansinė rizika (€)'].sum(),2)}</p>")
        html_parts.append(f"<p style='color:red;'>Kritinių klaidų skaičius: {(klaidos_df['Klaidos sunkumas'] == 'Kritinė').sum()}</p></section>")

        # Slide 2 – Sunkumo grafikas
        fig1_html = pio.to_html(fig1, full_html=False, include_plotlyjs='cdn')
        html_parts.append(f"<section><h2>Klaidų pasiskirstymas pagal sunkumą</h2>{fig1_html}</section>")

        # Slide 3 – Proceso etapas grafikas
        fig2_html = pio.to_html(fig2, full_html=False, include_plotlyjs=False)
        html_parts.append(f"<section><h2>Klaidos pagal proceso etapą ir sunkumą</h2>{fig2_html}</section>")

        # Slide 4 – Taisymo laikas grafikas
        fig3_html = pio.to_html(fig3, full_html=False, include_plotlyjs=False)
        html_parts.append(f"<section><h2>Klaidų taisymo laikas (val)</h2>{fig3_html}</section>")

        # Slide 5 – Visos klaidos lentelė su spalvomis
        def color_sunkumas(val):
            return f'class="{val}"'
        klaidos_html = klaidos_df.to_html(index=False, escape=False)
        for sunkumas in ["Kritinė","Vidutinė","Maža","Administracinė"]:
            klaidos_html = klaidos_html.replace(f">{sunkumas}<", f' {color_sunkumas(sunkumas)}>{sunkumas}<')
        html_parts.append(f"<section><h2>Visos klaidos</h2>{klaidos_html}</section>")

        html_parts.append("</div></div>")  # close slides + reveal

        # Init Reveal.js
        html_parts.append("""
        <script>
            Reveal.initialize({
                hash: true,
                slideNumber: true,
                width: "100%",
                height: "100%",
                transition: "slide"
            });
        </script>
        </body></html>
        """)

        full_html = "".join(html_parts)
        html_io = io.BytesIO(full_html.encode('utf-8'))
        st.success("Spalvota slide-like HTML ataskaita paruošta!")
        st.download_button("📥 Atsisiųsti HTML prezentaciją", html_io, file_name="Klaidu_ataskaita_slide_color.html")

else:
    st.info("Įkelkite Excel failą, kad pradėtume analizę")
