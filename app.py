# app.py – Klaidų analizė su rekomendacijomis, slide-like HTML
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
import io

st.set_page_config(page_title="Klaidų analizė", layout="wide")
st.title("📊 Klaidų analizė su rekomendacijomis ir slide-like HTML")

uploaded_file = st.file_uploader("Įkelkite Excel klaidų registrą", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # 1️⃣ Klaidos identifikacija
    df["Yra klaida"] = df["Klaidos tipas"].notna() & (df["Klaidos tipas"].astype(str).str.strip() != "")
    klaidos_df = df[df["Yra klaida"]].copy()

    # 2️⃣ Finansinė rizika pagal sumą ir klaidos tipą
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

    # 3️⃣ Taisymo laikas HH:MM:SS
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

    # 4️⃣ Klaidos sunkumas
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

    spalvos = {
        "Kritinė": "red",
        "Vidutinė": "orange",
        "Maža": "green",
        "Administracinė": "gray"
    }

    # 5️⃣ KPI
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📌 Tikrų klaidų skaičius", len(klaidos_df))
    col2.metric("⏱️ Prarastas laikas (val)", round(klaidos_df["Taisymo laikas (val)"].sum(), 2))
    col3.metric("💰 Bendra finansinė rizika (€)", round(klaidos_df["Finansinė rizika (€)"].sum(), 2))
    col4.metric("🔥 Kritinių klaidų", (klaidos_df["Klaidos sunkumas"] == "Kritinė").sum())

    # 6️⃣ Grafikai
    fig1 = px.bar(
        klaidos_df.groupby("Klaidos sunkumas").size().reset_index(name="Kiekis"),
        x="Klaidos sunkumas", y="Kiekis",
        color="Klaidos sunkumas",
        color_discrete_map=spalvos,
        title="Klaidų pasiskirstymas pagal sunkumą"
    )

    etapas_sunkumas = klaidos_df.groupby(["Proceso etapas","Klaidos sunkumas"]).size().reset_index(name="Kiekis")
    fig2 = px.bar(
        etapas_sunkumas,
        x="Proceso etapas", y="Kiekis",
        color="Klaidos sunkumas",
        color_discrete_map=spalvos,
        title="Klaidos pagal proceso etapą ir sunkumą"
    )

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

    # 7️⃣ Rekomendacijos
    rekomendacijos = {
        "Kritinė": "Imtis neatidėliotinų veiksmų, surinkti komandą ir peržiūrėti procesus.",
        "Vidutinė": "Peržiūrėti procesus ir optimizuoti klaidų prevenciją.",
        "Maža": "Sekti tendencijas, gali būti administracinės klaidos.",
        "Administracinė": "Tik administracinė priežiūra, nereikia skubaus veiksmo."
    }

    klaidos_df["Rekomendacija"] = klaidos_df["Klaidos sunkumas"].map(rekomendacijos)

    # 8️⃣ Generavimas slide-like HTML
    if st.button("📤 Generuoti interaktyvią slide-like HTML ataskaitą su rekomendacijomis"):
        html_parts = []
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

        # KPI slide
        html_parts.append("<section><h1>KPI</h1>")
        html_parts.append(f"<p>Tikrų klaidų skaičius: {len(klaidos_df)}</p>")
        html_parts.append(f"<p>Prarastas laikas (val): {round(klaidos_df['Taisymo laikas (val)'].sum(),2)}</p>")
        html_parts.append(f"<p>Bendra finansinė rizika (€): {round(klaidos_df['Finansinė rizika (€)'].sum(),2)}</p>")
        html_parts.append(f"<p style='color:red;'>Kritinių klaidų skaičius: {(klaidos_df['Klaidos sunkumas'] == 'Kritinė').sum()}</p></section>")

        # Grafikai
        for fig, title in zip([fig1, fig2, fig3], ["Pasiskirstymas pagal sunkumą","Proceso etapas","Taisymo laikas"]):
            fig_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
            html_parts.append(f"<section><h2>{title}</h2>{fig_html}</section>")

        # Lentelė su rekomendacijomis
        klaidos_html = klaidos_df.to_html(index=False, escape=False, table_id="klaidosTable")
        for sunkumas in ["Kritinė","Vidutinė","Maža","Administracinė"]:
            klaidos_html = klaidos_html.replace(f">{sunkumas}<", f' class="{sunkumas}">{sunkumas}<')
        html_parts.append(f"<section><h2>Visos klaidos su rekomendacijomis</h2>{klaidos_html}</section>")

        # JS filtravimas (tik sunkumas ir etapas, rekomendacija visada matosi)
        html_parts.append("""
        <section>
        <h2>Filtrai</h2>
        <label>Sunkumas:</label>
        <select id="sunkumasFilter" onchange="filterTable()">
            <option value="all">Visi</option>
            <option value="Kritinė">Kritinė</option>
            <option value="Vidutinė">Vidutinė</option>
            <option value="Maža">Maža</option>
            <option value="Administracinė">Administracinė</option>
        </select>
        <label>Proceso etapas:</label>
        <select id="etapasFilter" onchange="filterTable()">
            <option value="all">Visi</option>
        """ + "".join([f'<option value="{et}">{et}</option>' for et in klaidos_df['Proceso etapas'].unique()]) + """
        </select>
        </section>
        <script>
        function filterTable() {
            var sunkumas = document.getElementById("sunkumasFilter").value;
            var etapas = document.getElementById("etapasFilter").value;
            var table = document.getElementById("klaidosTable");
            var trs = table.getElementsByTagName("tr");
            for (var i = 1; i < trs.length; i++) {
                var tds = trs[i].getElementsByTagName("td");
                var rowSunkumas = tds[tds.length-2].textContent.trim(); // Klaidos sunkumas stulpelis
                var rowEtapas = tds[2].textContent.trim();              // Proceso etapas stulpelis
                var show = true;
                if (sunkumas != "all" && rowSunkumas != sunkumas) show = false;
                if (etapas != "all" && rowEtapas != etapas) show = false;
                trs[i].style.display = show ? "" : "none"; // Rekomendacija visada matosi
            }
        }
        </script>
        """)

        # Reveal init
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
        </div></div></body></html>
        """)

        full_html = "".join(html_parts)
        html_io = io.BytesIO(full_html.encode('utf-8'))
        st.success("Interaktyvi slide-like HTML ataskaita su rekomendacijomis paruošta!")
        st.download_button("📥 Atsisiųsti HTML prezentaciją", html_io, file_name="Klaidu_ataskaita_slide_rekomendacijos.html")

else:
    st.info("Įkelkite Excel failą, kad pradėtume analizę")
