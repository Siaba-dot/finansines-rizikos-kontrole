
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Finansinės rizikos kontrolė", layout="wide")

st.title("💰 Finansinės rizikos kontrolė")
st.write("Įkelk Excel failą ir sistema automatiškai atliks klaidų bei rizikos analizę.")

# -------------------------------------
# PAGALBINĖS FUNKCIJOS
# -------------------------------------

def normalize_cols(df):
    df.columns = [c.strip().replace("\n", " ").replace("  ", " ") for c in df.columns]
    return df

def to_dt(x):
    try:
        return pd.to_datetime(x, errors="coerce", infer_datetime_format=True)
    except:
        return pd.NaT

def to_num(x):
    if pd.isna(x): return np.nan
    if isinstance(x, (float, int)): return float(x)
    s = str(x).lower().replace("€", "").replace("eur", "").replace(",", ".")
    filt = "".join(ch for ch in s if ch.isdigit() or ch in ".-")
    try:
        return float(filt) if filt not in ["", ".", "-"] else np.nan
    except:
        return np.nan

def derive_fix_minutes(row):
    if not pd.isna(row.get("Taisymo laikas (min)")):
        return row["Taisymo laikas (min)"]
    s = row.get("Klaidos ištaisymo laiko pradžia")
    e = row.get("Klaidos ištaisymo laiko pabaiga")
    if isinstance(s, pd.Timestamp) and isinstance(e, pd.Timestamp):
        return (e - s).total_seconds() / 60
    return np.nan

def derive_fin_risk(row):
    if not pd.isna(row.get("Finansinė rizika")):
        return row["Finansinė rizika"]
    amount = row.get("Suma EUR, be PVM")
    severity = str(row.get("Klaidos sunkumas", "")).lower()
    coef = {"kritine": 0.30, "aukšta": 0.15, "vidutinė": 0.07, "žema": 0.03}.get(severity, 0.05)
    if not pd.isna(amount):
        return amount * coef
    return np.nan

# -------------------------------------
# ĮKĖLIMAS
# -------------------------------------

uploaded = st.file_uploader("Įkelk Excel (.xlsx) failą", type=["xlsx"])

if uploaded is None:
    st.info("Įkelk Excel failą, kad pradėti analizę.")
    st.stop()

try:
    sheet_names = pd.ExcelFile(uploaded).sheet_names
except Exception as e:
    st.error(f"Nepavyko perskaityti Excel: {e}")
    st.stop()

sheet = st.selectbox("Pasirink sheet", sheet_names)

df = pd.read_excel(uploaded, sheet_name=sheet)
df = normalize_cols(df)

rename_map = {
    "Suma EUR, be PVM": "Suma EUR, be PVM",
    "Taisymo laikas (min)": "Taisymo laikas (min)",
    "Finansinė rizika": "Finansinė rizika",
    "Klaidos tipas": "Klaidos tipas",
    "Dokumento gavimo data": "Dokumento gavimo data",
    "Dokumento data": "Dokumento data",
    "Klaidos ištaisymo laiko pradžia": "Klaidos ištaisymo laiko pradžia",
    "Klaidos ištaisymo laiko pabaiga": "Klaidos ištaisymo laiko pabaiga",
    "Klaidos sunkumas": "Klaidos sunkumas",
}
df = df.rename(columns=rename_map)

# Konversijos
for c in ["Dokumento data", "Dokumento gavimo data", "Klaidos ištaisymo laiko pradžia", "Klaidos ištaisymo laiko pabaiga"]:
    if c in df.columns:
        df[c] = df[c].apply(to_dt)

for c in ["Suma EUR, be PVM", "Taisymo laikas (min)", "Finansinė rizika"]:
    if c in df.columns:
        df[c] = df[c].apply(to_num)

# Išvestiniai
df["Taisymo laikas (min)"] = df.apply(derive_fix_minutes, axis=1)
df["Finansinė rizika"] = df.apply(derive_fin_risk, axis=1)

# -------------------------------------
# KPI
# -------------------------------------

st.subheader("🔎 Pagrindiniai KPI")

total_errors = len(df)
total_fix_min = np.nansum(df["Taisymo laikas (min)"]) if "Taisymo laikas (min)" in df.columns else 0
total_fix_hours = total_fix_min / 60 if total_fix_min else 0
total_risk = np.nansum(df["Finansinė rizika"]) if "Finansinė rizika" in df.columns else 0

c1, c2, c3 = st.columns(3)
c1.metric("Klaidų skaičius", total_errors)
c2.metric("Taisymo laikas (val.)", f"{total_fix_hours:.1f}")
c3.metric("Finansinė rizika (€)", f"{total_risk:,.2f}")

# -------------------------------------
# PARETO
# -------------------------------------

st.subheader("📌 Pareto analizė (klaidų tipai)")

if "Klaidos tipas" in df.columns and len(df) > 0:
    pareto = df["Klaidos tipas"].value_counts().reset_index()
    pareto.columns = ["Klaidos tipas", "Kiekis"]

    fig = px.bar(pareto, x="Klaidos tipas", y="Kiekis", title="Klaidų pasiskirstymas", text="Kiekis")
    st.plotly_chart(fig, use_container_width=True)
else:
       st.warning("Excel faile nėra stulpelio „Klaidos tipas“.")

# -------------------------------------
# TRENDAS
# -------------------------------------

st.subheader("📅 Trendas laike")

date_col = None
if "Dokumento gavimo data" in df.columns:
    date_col = "Dokumento gavimo data"
elif "Dokumento data" in df.columns:
    date_col = "Dokumento data"

if date_col:
    df["Periodas"] = df[date_col].dt.to_period("M").astype(str)
    trend = df.groupby("Periodas").size().reset_index(name="Kiekis")

    fig = px.line(trend, x="Periodas", y="Kiekis", markers=True, title="Klaidų skaičius per mėnesius")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nerasta datos stulpelių – trendas negalėjo būti sugeneruotas.")

# -------------------------------------
# BAIGTAS
# -------------------------------------

