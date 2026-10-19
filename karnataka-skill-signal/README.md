# Karnataka Skill Signal
## An Explainable Labour Market Intelligence System for Evidence-Based Skill Planning
### KSISU Skillathon 2026

**Team:** Shreyas Salian & Kaashvi Fatehpuria — M.S. Ramaiah University of Applied Sciences  
**Mentor:** Mr. Vishwanath K Reddy, Asst. Professor, ECE, M.S. Ramaiah University of Applied Sciences

---

## Project Objective

Karnataka Skill Signal transforms fragmented public training, historical workforce, and economic
datasets into transparent, reproducible analytical evidence. It helps Karnataka investigate
potential skill-alignment concerns by providing officials with clearly explainable indicators —
each showing exactly what it can and cannot establish.

**This is a decision-support prototype, not an operational government system.**
No skill shortage, employer demand, placement outcome, or causal relationship is claimed
unless the data actually establishes it.

---

## Data Sources

Place the following files in the workspace root directory (or set `DATA_DIR`):

| File | Source | Period |
|------|--------|--------|
| `GTTC_Shortterm_Courses.csv` | GTTC, Govt. of Karnataka | FY 2018–19 to 2021–22 |
| `GTTC_Number_of_Students_Passed_2019-2021_0.csv` | GTTC, Govt. of Karnataka | Calendar 2019–2021 |
| `census_2011_ddw_b06_2900_2011.csv` | RGI, India (censusindia.gov.in) | Census 2011 |
| `TotalEnrollmentbyLevel_2020-21.csv` | School-education MIS (unverified) | AY 2020–21 |
| `ManagementWiseClasswiseEnrolment2018_2019_1.csv` | Unverified publisher | AY 2018–19 |
| `State_Level_Single_Window_Committee_Industrydetails_2021.csv` | Unverified publisher | FY 2020–21 |

Raw files are never modified by the application.

---

## Local Installation

### Prerequisites
- Python 3.10+
- pip

### 1. Install Python dependencies

```bash
cd karnataka-skill-signal
pip install -r requirements.txt
```

### 2. Place data files

Ensure all six CSV files are in the workspace root
(`c:\Users\shrey\OneDrive\Desktop\ksisu 2026\` by default).

Alternatively, set the `DATA_DIR` environment variable:
```powershell
$env:DATA_DIR = "C:\path\to\your\data"
```

### 3. Start the API server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

### 4. Open the frontend

Open `frontend/index.html` directly in your browser, or serve it with any static file server:

```bash
# Python built-in server (from the frontend directory)
cd frontend
python -m http.server 8080
```

Then open `http://localhost:8080`.

**Important:** The frontend expects the API at `http://localhost:8000`.
If your API runs elsewhere, edit the `window.KSS_API_BASE` line in `frontend/index.html`.

---

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

All 26 tests should pass, verifying:
- Dataset availability
- GTTC annual totals (1,040 / 2,515 / 2,086 / 2,420 → grand total 8,061)
- Like-for-like cohort (Mysuru, Dandeli, Kalaburgi)
- Cell coverage (23 of 40 = 57.5%)
- Siemens partner total (6,655)
- Census total persons (4,473,682) and 30 districts
- SLSWCC 307 units and 85,694 listed employment
- Quality check execution

---

## Deployment

### Frontend (Static)

Deploy `frontend/` to Vercel, Netlify, GitHub Pages, or any static host.

Before deploying, update the API URL in `frontend/index.html`:
```html
<script>
  window.KSS_API_BASE = "https://your-api-host.com";
</script>
```

### Backend (Python API)

Deploy to Render, Railway, Fly.io, or any Python-capable host.

Environment variables:
```
DATA_DIR=/path/to/csv/files
CORS_ORIGINS=https://your-frontend.vercel.app
PORT=8000
```

Start command:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Indicator Definitions

| ID | Name | Formula | Status |
|----|------|---------|--------|
| I1 | Annual Training Activity | A(t) = Σ centre counts in year t | Implemented |
| I2 | Year-over-Year Change | [A(t) − A(t−1)] ÷ A(t−1) × 100 | Implemented |
| I3 | Centre Concentration | Share(c) = N(c) ÷ ΣN | Implemented |
| I4 | Completion / Pass Rate | Passed ÷ Enrolled (same course, centre, year) | **Not computable** — no denominator in files |
| I5 | Potential Alignment Flag | Flag when sector employment-signal share high AND training share low | **Proposed** — requires crosswalk |
| I6 | Completeness and Freshness | Filled cells ÷ Expected cells | Implemented |

**No composite SkillGap Index is claimed.** Flags are prompts for investigation, not proofs of shortage.

---

## Known Data-Quality Issues

- **GTTC count unit undefined:** No data dictionary defines what the short-term count represents.
- **GTTC files appear to be one source:** CoE row in the passed-out file equals GTTC yearly totals.
- **23/40 GTTC centre-year cells filled (57.5%):** Blanks are not converted to zero.
- **District name/boundary changes:** Census 2011 uses 30 districts with 2011 boundaries; later files use different names. A versioned crosswalk is required for multi-source joins.
- **One corrupted enrolment cell:** "56972700%" in TotalEnrollmentbyLevel — recoverable as 569,727.
- **SLSWCC employment is listed employment from approved projects**, not realised jobs or vacancies. 8 units list zero employment.
- **2021 Diploma count** in GTTC passed file is "YET TO COMPILE".
- **Manufacturing service order value (2020):** File shows ₹126.8 lakh (note: slide 6 cited ₹187.5 — the CSV value is 126.8).

---

## Project Structure

```
karnataka-skill-signal/
├── frontend/
│   ├── index.html          # Main HTML page (all sections)
│   ├── styles.css          # Design system and component styles
│   └── app.js              # API fetching, chart rendering, interactions
├── backend/
│   ├── main.py             # FastAPI app with all endpoints
│   ├── data_loader.py      # Loads and validates each CSV
│   ├── analytics.py        # Computes indicators from loaded data
│   ├── validation.py       # Data-quality checks
│   └── tests/
│       ├── __init__.py
│       └── test_analytics.py  # 26 unit tests
├── data/
│   └── README.md           # Data file placement instructions
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## AI Assistance Disclosure

Claude (Anthropic) assisted with data analysis, code development, and documentation.
All figures were computed from the cited government CSVs and verified by the team
using `skill_signal_verification.py` (26/26 assertions pass).
