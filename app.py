
# -*- coding: utf-8 -*-
import os
import re
from datetime import timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ------------------------------
# PUSLAPIO NUSTATYMAI
# ------------------------------
st.set_page_config(page_title="Finansinės rizikos kontrolė", layout="wide")

st.title("💰 Finansinės rizikos kontrolė")
st.write("Įkelk Excel (.xlsx) failą – sistema automatiškai atliks klaidų ir rizikos analizę.")

# ------------------------------
# PAGALBINĖS FUNKCIJOS
# ------------------------------
def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().replace("\n", " ").replace("  ", " ") for c in df.columns]
    return df

def to_dt(x):
    """Tvirtas datų parsinimas su dayfirst=True (LT įprasta)."""
    try:
        return pd.to_datetime(x, errors="coerce", dayfirst=True)
    except Exception:
        return pd.NaT

def to_num(x):
    """
    Patikimas EUR sumų parsinimas:
    - pašalina valiutos tekstą/simbolius (EUR, €)
    - panaikina tūkstančių skyriklius (tarpus ir taškus)
    - kablelį paverčia į tašką (europinis formatas)
    Pvz.: '2.404,75 €' -> 2404.75
    """
    if pd.isna(x):
        return np.nan
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)
    s = str(x).strip().lower()
    s = s.replace("eur", "").replace("€", "").replace("eur.", "").strip()
    # paliekam tik leistinus simbolius
    s = re.sub(r"[^0-9\-,.\s]", "", s)
    # nuimam tarpus (tūkstančių skyrikliai)
    s = s.replace(" ", "")
    # jei ir taškai, ir kablelis ir kablelis eina vėliau nei paskutinis taškas -> taškai=tūkst., kablelis=dešimtosios
    if "," in s and "." in s and s.rfind(",") > s.rfind("."):
        s = s.replace(".", "")
        s = s.replace(",", ".")
    else:
        # jei tik kablelis – paversk kablelį į tašką
        if "," in s and "." not in s:
            s = s.replace(",", ".")
    # normalizuojam minusą: paliekam tik pirmą ženklą eilutės pradžioje
    s = re.sub(r"(?<!^)-", "", s)
    try:
        return float(s)
    except Exception:
        return np.nan

def normalize_severity(s):
    """Suvienodina sunkumo reikšmes į: 'kritine', 'auksta', 'vidutine', 'zema'."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    s = str(s).strip().lower()
    repl = {
        "ą": "a", "č": "c", "ę": "e", "ė": "e", "į": "i", "š": "s", "ų": "u", "ū": "u", "ž": "z",
        "á": "a", "à": "a", "ä": "a", "é": "e", "è": "e", "ë": "e", "í": "i", "ì": "i", "ï": "i",
        "ó": "o", "ò": "o", "ö": "o", "ú": "u", "ù": "u", "ü": "u"
    }
    s = "".join(repl.get(ch, ch) for ch in s)
    m = {
        "kritine": "kritine", "kritinis": "kritine",
        "auksta": "auksta", "aukstas": "auksta",
        "vidutine": "vidutine", "vidutinis": "vidutine",
        "zema": "zema", "zemas": "zema",
    }
    return m.get(s, s)

def derive_fix_minutes(row):
    """
    Skaičiuoja taisymo laiką minutėmis:
    - jei pabaiga < pradžia, laikoma, kad perėjo per vidurnaktį (pridedama 1 d.)
    - grąžina NaN, jei trūksta datų
    - atmeta absurdiškas reikšmes (> 16 val.)
    """
    # jei jau yra įrašyta reikšmė – paliekam
    if not pd.isna(row.get("Taisymo laikas (min)")):
        return row["Taisymo laikas (min)"]

    s = row.get("Klaidos ištaisymo laiko pradžia")
    e = row.get("Klaidos ištaisymo laiko pabaiga")

    if isinstance(s, pd.Timestamp) and isinstance(e, pd.Timestamp):
        if pd.isna(s) or pd.isna(e):
            return np.nan
        if e < s:
            e = e + timedelta(days=1)
        minutes = (e - s).total_seconds() / 60.0
        if minutes < 0 or minutes > 16 * 60:
            return np.nan
        return minutes
    return np.nan

def derive_fin_risk(row, coef_map):
    # jei jau yra reikšmė – neliečiam
    if not pd.isna(row.get("Finansinė rizika")):
        return row["Finansinė rizika"]
    amount = row.get("Suma EUR, be PVM")
    severity = normalize_severity(row.get("Klaidos sunkumas", ""))
    coef = coef_map.get(severity, 0.05)  # default, jei neatpažįsta
    return amount * coef if not pd.isna(amount) else np.nan

# ------------------------------
# ŠONINIS MENIU – koeficientai
# ------------------------------
st.sidebar.header("Rizikos koeficientai")
k_coef  = st.sidebar.number_input("Kritinė (%)", value=30.0, min_value=0.0, max_value=100.0, step=1.0) / 100.0
ah_coef = st.sidebar.number_input("Aukšta (%)",  value=15.0, min_value=0.0, max_value=100.0, step=1.0) / 100.0
v_coef  = st.sidebar.number_input("Vidutinė (%)", value=7.0,  min_value=0.0, max_value=100.0, step=0.5) / 100.0
z_coef  = st.sidebar.number_input("Žema (%)",    value=3.0,  min_value=0.0, max_value=100.0, step=0.5) / 100.0

COEF_MAP = {"kritine": k_coef, "auksta": ah_coef, "vidutine": v_coef, "zema": z_coef}

# ------------------------------
# ĮKĖLIMAS
# ------------------------------
uploaded = st.file_uploader("Įkelk Excel (.xlsx) failą", type=["xlsx"], accept_multiple_files=False)

if uploaded is None:
    st.info("Įkelk Excel failą, kad pradėti analizę.")
    st.stop()

# Aiškiai nurodom openpyxl ir tvarkom srautą
try:
    uploaded.seek(0)
    xl = pd.ExcelFile(uploaded, engine="openpyxl")
    sheet_names = xl.sheet_names
except Exception as e:
    st.error(f"Nepavyko perskaityti Excel: {e}")
    st.stop()

sheet = st.selectbox("Pasirink sheet", sheet_names)

uploaded.seek(0)
df = pd.read_excel(uploaded, sheet_name=sheet, engine="openpyxl")
df = normalize_cols(df)

# Stulpelių žemėlapis (paliktas, jei reikėtų pervadinimų)
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

# Pervadinimai (saugiai)
for k, v in rename_map.items():
    if k in df.columns:
        df.rename(columns={k: v}, inplace=True)

# Konversijos – datos
for c in [
    "Dokumento data",
    "Dokumento gavimo data",
    "Klaidos ištaisymo laiko pradžia",
    "Klaidos ištaisymo laiko pabaiga",
]:
    if c in df.columns:
        df[c] = df[c].apply(to_dt)

# Konversijos – skaičiai
for c in ["Suma EUR, be PVM", "Taisymo laikas (min)", "Finansinė rizika"]:
    if c in df.columns:
        df[c] = df[c].apply(to_num)

# Išvestiniai laukai
if "Taisymo laikas (min)" in df.columns or (
    "Klaidos ištaisymo laiko pradžia" in df.columns and "Klaidos ištaisymo laiko pabaiga" in df.columns
):
    df["Taisymo laikas (min)"] = df.apply(derive_fix_minutes, axis=1)

if "Suma EUR, be PVM" in df.columns:
    df["Finansinė rizika"] = df.apply(lambda r: derive_fin_risk(r, COEF_MAP), axis=1)

# ------------------------------
# DIAGNOSTIKA
# ------------------------------
with st.expander("🔍 Diagnostika: duomenų peržiūra", expanded=False):
    cols_show = [
        c
        for c in [
            "Suma EUR, be PVM",
            "Klaidos sunkumas",
            "Finansinė rizika",
            "Taisymo laikas (min)",
            "Klaidos ištaisymo laiko pradžia",
            "Klaidos ištaisymo laiko pabaiga",
        ]
        if c in df.columns
    ]
    if cols_show:
        st.dataframe(df[cols_show].head(100), use_container_width=True)

    # Outlier'iai trukmėse
    if "Taisymo laikas (min)" in df.columns:
        outliers = df[(df["Taisymo laikas (min)"] < 0) | (df["Taisymo laikas (min)"] > 8 * 60)]
        if len(outliers) > 0:
            st.warning("Rasta trukmės outlier'ių (> 8 val. arba < 0):")
            st.dataframe(outliers[cols_show], use_container_width=True)

    # Probleminės sumos/rizikos
    if all(c in df.columns for c in ["Suma EUR, be PVM", "Finansinė rizika"]):
        sus = df[df["Suma EUR, be PVM"].isna() | df["Finansinė rizika"].isna()]
        if len(sus) > 0:
            st.info("Eilutės su neparsinamomis sumomis/rizika:")
            st.dataframe(sus[cols_show], use_container_width=True)

# ------------------------------
# KPI
# ------------------------------
st.subheader("🔎 Pagrindiniai KPI")

# Saugikliai nuo outlier'ių
if "Taisymo laikas (min)" in df.columns:
    fix_series = df["Taisymo laikas (min)"]
    safe_fix_series = fix_series[(fix_series >= 0) & (fix_series <= 16 * 60)]
    total_fix_min = float(np.nansum(safe_fix_series))
else:
    total_fix_min = 0.0

total_errors = int(len(df))


# Saugikliai nuo outlier'ių (rizika)
if "Finansinė rizika" in df.columns:
    # BŪTINA: viena eilutė, paprastos kabutės
    risk_series = df["Finansinė rizika"].where(df["Finansinė rizika"].between(0, 1e9))
    total_risk = float(np.nansum(risk_series))
else:
    total_risk = 0.0

total_fix_hours = total_fix_min / 60.0 if total_fix_min else 0.0

c1, c2, c3 = st.columns(3)
c1.metric("Klaidų skaičius", total_errors)
c2.metric("Taisymo laikas (val.)", f"{total_fix_hours:.1f}")
c3.metric("Finansinė rizika (€)", f"{total_risk:,.2f}")
