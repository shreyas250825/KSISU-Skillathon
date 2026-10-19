# Karnataka Skill Signal

**An Explainable Labour Market Intelligence System for Evidence-Based Skill Planning**

> KSISU Skillathon 2026 — Karnataka Skill Intelligence and Strategy Unit

---

## 🌐 Live Site

**[https://ksisu.netlify.app](https://ksisu.netlify.app)**

---

## The Team

| Name | Role | Institution |
|---|---|---|
| **Shreyas Salian** | Project Lead / Participant 1 | M.S. Ramaiah University of Applied Sciences |
| **Kaashvi Fatehpuria** | Participant 2 | M.S. Ramaiah University of Applied Sciences |
| **Mr. Vishwanath K Reddy** | Mentor | Asst. Professor, ECE, M.S. Ramaiah University of Applied Sciences |

---

## What this is

Karnataka's training, workforce, and economic data sit in separate files with different
periods, units, and geographies. Planners cannot compare them directly — and fragmented
data invites over-interpretation.

**Karnataka Skill Signal** is a transparent, reproducible analytical prototype that
brings three evidence streams together in one place:

| Stream | What it shows | What it cannot tell you |
|---|---|---|
| **Training activity** | GTTC CoE reported counts by centre, year, partner | Employer demand, placement, quality |
| **Historical workforce** | Census 2011 marginal workers by industry, gender, age | Current labour demand or vacancies |
| **Economic signals** | SLSWCC approved-project investment and listed employment | Realised jobs or current vacancies |

Every indicator shows its formula, its source, and exactly what it cannot establish.
No black-box scores. No invented skill gaps.

> **This is a decision-support prototype — not an operational government system.**

---

## Project Structure

```
karnataka-skill-signal/
│
├── frontend/               ← Static site deployed to Netlify
│   ├── index.html          ← Single-page application (all 10 sections)
│   ├── styles.css          ← Design system (warm ivory / sage green / terracotta)
│   ├── app.js              ← Chart rendering, tab logic, tables, exports
│   └── data_bundle.js      ← Pre-computed analytics (no backend needed)
│
├── backend/                ← Python API for local development
│   ├── main.py             ← FastAPI app (12 endpoints + OpenAPI docs at /docs)
│   ├── data_loader.py      ← Loads and validates each CSV, never modifies them
│   ├── analytics.py        ← Computes all indicators with transparent formulas
│   ├── validation.py       ← Data-quality checks (PASS / WARNING / FAIL)
│   └── tests/
│       └── test_analytics.py  ← 26 unit tests (all pass)
│
├── data/                   ← All six source CSV files
│   ├── GTTC_Shortterm_Courses.csv
│   ├── GTTC_Number_of_Students_Passed_2019-2021_0.csv
│   ├── census_2011_ddw_b06_2900_2011.csv
│   ├── TotalEnrollmentbyLevel_2020-21.csv
│   ├── ManagementWiseClasswiseEnrolment2018_2019_1.csv
│   └── State_Level_Single_Window_Committee_Industrydetails_2021.csv
│
├── netlify.toml            ← Tells Netlify to serve frontend/
├── requirements.txt        ← Python dependencies
├── .env.example            ← Environment variable reference
└── README.md               ← This file
```

---

## Data Sources

All files are in `data/`. Loaded exactly as provided — never modified.

| File | Publisher | Period |
|---|---|---|
| `GTTC_Shortterm_Courses.csv` | GTTC, Govt. of Karnataka *(catalogue page unverified)* | FY 2018–19 to 2021–22 |
| `GTTC_Number_of_Students_Passed_2019-2021_0.csv` | GTTC, Govt. of Karnataka *(catalogue page unverified)* | Calendar 2019–2021 |
| `census_2011_ddw_b06_2900_2011.csv` | Registrar General & Census Commissioner, India | Census 2011 |
| `TotalEnrollmentbyLevel_2020-21.csv` | School-education MIS *(publisher unverified)* | AY 2020–21 |
| `ManagementWiseClasswiseEnrolment2018_2019_1.csv` | *(Publisher unverified)* | AY 2018–19 |
| `State_Level_Single_Window_Committee_Industrydetails_2021.csv` | *(Publisher unverified)* | FY 2020–21 |

---

## Verified Numbers

Computed from actual CSVs, checked by 26 automated unit tests.

| Metric | Value | Source |
|---|---|---|
| GTTC cumulative reported count | **8,061** | GTTC_Shortterm_Courses.csv |
| GTTC annual counts | **1,040 / 2,515 / 2,086 / 2,420** | GTTC_Shortterm_Courses.csv |
| Like-for-like cohort (3 centres) | **1,040 / 2,071 / 975 / 1,641** | GTTC_Shortterm_Courses.csv |
| Cell coverage | **23 of 40 = 57.5%** | GTTC_Shortterm_Courses.csv |
| Siemens-CoE share | **82.6%** (6,655 of 8,061) | GTTC_Shortterm_Courses.csv |
| Mysuru share | **34.6%** | GTTC_Shortterm_Courses.csv |
| Census marginal workers (Karnataka) | **4,473,682** | Census 2011 Table B-06 |
| Census districts | **30** | Census 2011 |
| Agriculture share of marginal workers | **~63.7%** | Census 2011 |
| SLSWCC approved units | **307** | SLSWCC 2021 |
| SLSWCC listed employment | **85,694** | SLSWCC 2021 |
| SLSWCC total investment | **₹15,270.66 Cr** | SLSWCC 2021 |

---

## Indicators

| ID | Name | Formula | Status |
|---|---|---|---|
| **I1** | Annual Reported Training Activity | A(t) = Σ centre counts in year t | ✅ Implemented |
| **I2** | Year-over-Year Change | [A(t) − A(t−1)] ÷ A(t−1) × 100 | ✅ Implemented |
| **I3** | Centre Concentration | Share(c) = N(c) ÷ ΣN | ✅ Implemented |
| **I4** | Completion / Pass Rate | Passed ÷ Enrolled | ❌ Not computable — no enrolment denominator in files |
| **I5** | Potential Alignment Flag | High economic share + low training share | 🔲 Proposed — needs crosswalk |
| **I6** | Completeness and Freshness | Filled cells ÷ Expected cells | ✅ Implemented |

**No composite SkillGap Index is claimed.**

---

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Start the API (from backend/)
cd karnataka-skill-signal/backend
uvicorn main:app --reload --port 8000
# API docs → http://localhost:8000/docs

# Open the frontend — just open frontend/index.html in your browser
# (works without the backend thanks to the embedded data bundle)

# Run tests
python -m pytest tests/ -v
```

---

## Deploying to Netlify

```
Site:      https://ksisu.netlify.app
Deploy:    Drag frontend/ to app.netlify.com/drop
           — or connect GitHub repo, set publish directory = frontend
```

---

## Known Data-Quality Issues

| Issue | Detail |
|---|---|
| GTTC count unit undefined | No data dictionary defines what the count represents |
| GTTC files appear to be one source | CoE row in passed-out file equals GTTC yearly totals |
| 57.5% cell coverage | 23 of 40 centre-year cells filled; blanks ≠ zero |
| District boundary changes | Census 2011 uses 30 districts; later files differ — crosswalk needed |
| Corrupted enrolment cell | "56972700%" → recoverable as 569,727 (Bengaluru U South) |
| SLSWCC employment ≠ jobs | Listed from approved-project forms; 8 units list zero |
| 2021 Diploma count | Marked "YET TO COMPILE" in source file |

---

## Roadmap

| Phase | Focus |
|---|---|
| **Phase 1** *(done)* | Public-data prototype, indicators I1–I3 and I6, quality checks, dashboard |
| **Phase 2** | ITI data, Udyam/MSME, employer surveys, district code crosswalk, trade→sector map |
| **Phase 3** | Automated refresh, portal MIS and Jobs module integration, role-based access |
| **Phase 4** | Pilot in selected districts, expert validation, responsible scaling |

---

## AI Assistance Disclosure

Claude (Anthropic) assisted with documentation.
All figures were computed from the cited government CSVs and verified by the team.

---

*Karnataka Skill Signal · KSISU Skillathon 2026 · M.S. Ramaiah University of Applied Sciences*
