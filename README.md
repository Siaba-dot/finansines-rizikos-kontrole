# 💰 Finansinės rizikos kontrolė

**Finansinės rizikos kontrolė** – tai Streamlit aplikacija, skirta analizuoti dokumentų klaidas, jų taisymo laiką ir finansinę riziką.  
Ji leidžia lengvai įkelti Excel (.xlsx) failą ir gauti aiškius KPI, vizualizacijas ir tendencijas.

🟢 Skirta vidiniam procesų valdymui  
🟢 Padeda identifikuoti pasikartojančias klaidas  
🟢 Parodo finansinę riziką ir realų poveikį įmonei  
🟢 Veikia Apps’o / Streamlit aplinkoje be jokių papildomų diegimų

---

## 🚀 Funkcionalumas

Aplikacija leidžia:

### 📂 Įkelti Excel (.xlsx) failą
- Pasirinkti reikiamą „sheet“
- Automatiškai konvertuoti datas, sumas ir laikus

### 📊 Pamatyti pagrindinius KPI:
- bendras klaidų skaičius
- taisymo laikas valandomis
- bendra finansinė rizika €

### 📌 Pareto analizė
Identifikuoja klaidų tipus, kurie daro didžiausią poveikį (80/20 principas).

### 📅 Trendas laike
- Klaidų skaičius per mėnesius
- Finansinės rizikos pokytis laikui bėgant

### 🔧 Automatinės konversijos
- Jei nėra „Taisymo laikas (min)“ → apskaičiuoja pagal pradžios/pabaigos laiką  
- Jei nėra „Finansinė rizika“ → paskaičiuoja konservatyvią riziką pagal sumą ir sunkumą

---

## 📥 Excel failo struktūra

Aplikacija veikia su bet kuriuo Excel, kuriame yra šie stulpeliai (nebūtinai visi):

| Stulpelis | Paskirtis |
|----------|-----------|
| `Klaidos tipas` | Pareto analizei |
| `Finansinė rizika` | Bendrai rizikai |
| `Suma EUR, be PVM` | Rizikos apskaičiavimui, jei nėra |
| `Taisymo laikas (min)` | KPI / darbo kaštams |
| `Klaidos ištaisymo laiko pradžia` | Taisymo laiko išvedimui |
| `Klaidos ištaisymo laiko pabaiga` | Taisymo laiko išvedimui |
| `Dokumento gavimo data` | Mėnesio trendams |
| `Dokumento data` | Alternatyva trendams |
|| `Klaidos sunkumas` | Rizikos koeficientui |


Jeigu kai kurie stulpeliai neegzistuoja – aplikacija paprasčiausiai praleis tą dalį.

---

## 🛠️ Paleidimas Appsa/Streamlit aplinkoje

### 1️⃣ Įkelkite šį repo į GitHub  
Pavadinimas: **finansines-rizikos-kontrole**

