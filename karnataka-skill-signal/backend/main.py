"""
main.py  ·  Karnataka Skill Signal — FastAPI backend
Run: uvicorn main:app --reload --port 8000
"""

import io
import csv
import json
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

import analytics
import validation
from data_loader import dataset_status, load_all, DATA_DIR

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Karnataka Skill Signal API",
    description=(
        "Transparent Labour Market Intelligence System for Evidence-Based Skill Planning. "
        "All indicators are computed from public government datasets. "
        "No black-box scores; every figure cites its source and limitation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ───────────────────────────────────────────────────────────────────────
ALLOWED_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost,http://localhost:3000,http://localhost:8080,http://127.0.0.1,null"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # open for prototype; restrict in production
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ── Helpers ────────────────────────────────────────────────────────────────────

def _require(data: dict):
    if not data.get("available", True):
        raise HTTPException(
            status_code=503,
            detail={
                "message": f"Dataset not available: {data.get('file', 'unknown')}",
                "resolution": f"Place the file in the data directory: {DATA_DIR}",
            },
        )
    return data


def _csv_response(rows: list, filename: str) -> StreamingResponse:
    if not rows:
        raise HTTPException(status_code=404, detail="No data to export.")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["System"])
def health():
    """Returns service health and dataset availability."""
    statuses = dataset_status()
    loaded = sum(1 for s in statuses if s["available"])
    return {
        "status": "ok",
        "datasets_loaded": loaded,
        "datasets_total": len(statuses),
        "data_directory": str(DATA_DIR),
    }


# ── Overview ───────────────────────────────────────────────────────────────────
@app.get("/api/overview", tags=["Overview"])
def overview():
    """Headline statistics and dataset status for the executive overview section."""
    return analytics.overview_stats()


# ── Datasets ──────────────────────────────────────────────────────────────────
@app.get("/api/datasets", tags=["Overview"])
def datasets():
    """List all expected datasets with availability and period metadata."""
    return {"datasets": dataset_status()}


# ── GTTC Short-term Courses ───────────────────────────────────────────────────
@app.get("/api/gttc/trends", tags=["GTTC"])
def gttc_trends(
    year: str = Query(None, description="Filter to a specific year, e.g. '2019-20'"),
    series: str = Query(None, description="Filter series: 'all' or 'lfl'"),
):
    """Annual trend data for GTTC short-term CoE courses (I1 and I2 indicators)."""
    data = analytics.gttc_trends()
    _require(data)

    # Filter trend series
    if series == "lfl":
        data["trend_series"] = [s for s in data["trend_series"] if "Like" in s["series"]]
    elif series == "all":
        data["trend_series"] = [s for s in data["trend_series"] if "Like" not in s["series"]]

    if year:
        data["trend_series"] = [s for s in data["trend_series"] if s["year"] == year]

    data["source"] = {
        "file": "GTTC_Shortterm_Courses.csv",
        "publisher": "GTTC, Govt. of Karnataka (catalogue page unverified)",
        "period": "FY 2018–19 to 2021–22",
        "unit_note": "Count unit is not defined in a data dictionary. Values labelled as 'reported counts'.",
    }
    return data


@app.get("/api/gttc/trends/export", tags=["GTTC"])
def gttc_trends_export():
    """Export GTTC annual trends as CSV."""
    data = analytics.gttc_trends()
    _require(data)
    return _csv_response(data["yoy_table"], "gttc_annual_trends.csv")


@app.get("/api/gttc/centres", tags=["GTTC"])
def gttc_centres(
    coe: str = Query(None, description="Filter by CoE partner name, e.g. 'Siemens- CoE'"),
    sort: str = Query("total", description="Sort by: 'total', 'name'"),
):
    """Centre-level breakdown for GTTC short-term CoE courses (I3 indicator)."""
    data = analytics.gttc_centres()
    _require(data)

    if coe:
        data["centres"] = [c for c in data["centres"] if c.get("coe") == coe]

    if sort == "name":
        data["centres"].sort(key=lambda x: x["centre"])

    data["source"] = {
        "file": "GTTC_Shortterm_Courses.csv",
        "publisher": "GTTC, Govt. of Karnataka (catalogue page unverified)",
        "period": "FY 2018–19 to 2021–22",
    }
    return data


@app.get("/api/gttc/centres/export", tags=["GTTC"])
def gttc_centres_export():
    """Export GTTC centre data as CSV."""
    data = analytics.gttc_centres()
    _require(data)
    return _csv_response(data["centres"], "gttc_centres.csv")


@app.get("/api/gttc/coverage", tags=["GTTC"])
def gttc_coverage():
    """Data completeness and GTTC passed-out programme breakdown (I6 indicator)."""
    data = analytics.gttc_coverage()
    _require(data)
    data["source"] = {
        "files": [
            "GTTC_Shortterm_Courses.csv",
            "GTTC_Number_of_Students_Passed_2019-2021_0.csv",
        ],
        "publisher": "GTTC, Govt. of Karnataka (catalogue pages unverified)",
    }
    return data


# ── Census ────────────────────────────────────────────────────────────────────
@app.get("/api/census/industry", tags=["Census"])
def census_industry(
    category: str = Query(None, description="Filter by industry category code, e.g. 'A'"),
    min_share: float = Query(None, description="Minimum share percent to include"),
):
    """Industry-level breakdown of Census 2011 marginal workers."""
    data = analytics.census_industry()
    _require(data)

    if category:
        data["categories"] = [c for c in data["categories"] if c["code"] == category]
    if min_share is not None:
        data["categories"] = [c for c in data["categories"] if c["share_pct"] >= min_share]

    data["source"] = {
        "file": "census_2011_ddw_b06_2900_2011.csv",
        "publisher": "Registrar General & Census Commissioner, India (censusindia.gov.in)",
        "period": "Census 2011",
        "limitation": "Marginal workers only; 2011 boundaries; NOT a measure of current employment demand.",
    }
    return data


@app.get("/api/census/industry/export", tags=["Census"])
def census_industry_export():
    """Export Census industry breakdown as CSV."""
    data = analytics.census_industry()
    _require(data)
    return _csv_response(data["categories"], "census_industry_breakdown.csv")


@app.get("/api/census/demographics", tags=["Census"])
def census_demographics():
    """Gender and age breakdown of Census 2011 marginal workers."""
    data = analytics.census_demographics()
    _require(data)
    data["source"] = {
        "file": "census_2011_ddw_b06_2900_2011.csv",
        "publisher": "Registrar General & Census Commissioner, India",
        "period": "Census 2011",
        "limitation": "Marginal workers only. Not current demand or vacancy data.",
    }
    return data


# ── Enrolment ─────────────────────────────────────────────────────────────────
@app.get("/api/enrolment/overview", tags=["Enrolment"])
def enrolment_overview():
    """School enrolment context — NOT vocational training capacity or employability."""
    data = analytics.enrolment_overview()
    return data


# ── SLSWCC ────────────────────────────────────────────────────────────────────
@app.get("/api/industry/overview", tags=["Industry"])
def industry_overview(
    sector: str = Query(None, description="Filter by sector name (case-insensitive partial match)"),
    min_employment: int = Query(None, description="Minimum sector employment to include"),
):
    """Single Window Committee approved-project industry signals (FY 2020–21)."""
    data = analytics.industry_overview()
    _require(data)

    if sector:
        data["sectors"] = [
            s for s in data["sectors"]
            if sector.upper() in s["SECTOR_CLEAN"].upper()
        ]
    if min_employment is not None:
        data["sectors"] = [s for s in data["sectors"] if s["employment"] >= min_employment]

    return data


@app.get("/api/industry/export", tags=["Industry"])
def industry_export():
    """Export SLSWCC sector breakdown as CSV."""
    data = analytics.industry_overview()
    _require(data)
    return _csv_response(data["sectors"], "slswcc_sectors.csv")


# ── Quality ────────────────────────────────────────────────────────────────────
@app.get("/api/quality/report", tags=["Quality"])
def quality_report():
    """Run all data-quality checks and return results with PASS/WARNING/FAIL/NOT_CHECKED."""
    return validation.run_all_checks()


# ── Methodology ───────────────────────────────────────────────────────────────
@app.get("/api/methodology", tags=["Methodology"])
def methodology():
    """Return indicator definitions, formulas, and limitations."""
    return {
        "indicators": analytics.methodology_indicators(),
        "pipeline_stages": [
            {"stage": 1, "name": "Raw Data", "status": "Implemented", "description": "Public CSV files loaded as-is; raw files never modified."},
            {"stage": 2, "name": "Schema Validation", "status": "Implemented", "description": "Column names, types, and expected row counts checked."},
            {"stage": 3, "name": "Missing-Value Checks", "status": "Implemented", "description": "Blank ≠ zero; completeness reported per dataset."},
            {"stage": 4, "name": "Standardisation", "status": "Implemented (partial)", "description": "Sector labels normalised; district names documented; corrupted cells flagged."},
            {"stage": 5, "name": "Geo-temporal Harmonisation", "status": "Proposed", "description": "District-code crosswalk with boundary year required for multi-source joins."},
            {"stage": 6, "name": "Sector / Trade Mapping", "status": "Proposed", "description": "Documented crosswalk from training trades to economic sectors."},
            {"stage": 7, "name": "Indicator Computation", "status": "Implemented", "description": "Transparent formulas for I1–I3, I6; I4 not computable; I5 proposed."},
            {"stage": 8, "name": "Validation", "status": "Implemented (partial)", "description": "Total reconciliation run; automated anomaly flags proposed."},
            {"stage": 9, "name": "Dashboard", "status": "Implemented (prototype)", "description": "Interactive frontend serving computed indicators."},
        ],
        "caveats": [
            "No composite SkillGap Index is claimed.",
            "Flags are prompts for investigation, not proofs of shortage.",
            "Every indicator states what it cannot establish.",
            "Officials must review indicators before any policy use.",
        ],
    }
