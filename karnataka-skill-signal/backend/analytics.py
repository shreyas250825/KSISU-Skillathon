"""
analytics.py
Computes derived indicators from loaded data.
Every formula is transparent; no black-box scores are produced.
"""

from __future__ import annotations
from data_loader import (
    load_gttc_courses, load_gttc_passed,
    load_census, load_enrolment_2021, load_slswcc, dataset_status
)


def overview_stats() -> dict:
    """Return headline numbers for the overview section."""
    gttc  = load_gttc_courses()
    cen   = load_census()
    slswcc = load_slswcc()
    statuses = dataset_status()
    loaded = sum(1 for s in statuses if s["available"])

    return {
        "datasets_loaded": loaded,
        "datasets_total": len(statuses),
        "indicators_computed": 6,
        "gttc_grand_total": gttc.get("grand_total") if gttc.get("available") else None,
        "gttc_years": "2018–19 to 2021–22",
        "census_total_persons": cen.get("total_persons") if cen.get("available") else None,
        "census_year": "2011",
        "slswcc_units": slswcc.get("n_units") if slswcc.get("available") else None,
        "slswcc_employment": slswcc.get("total_employment") if slswcc.get("available") else None,
        "slswcc_year": "FY 2020–21",
        "dataset_statuses": statuses,
    }


def gttc_trends() -> dict:
    """Return structured data for trend charts."""
    d = load_gttc_courses()
    if not d.get("available"):
        return d

    yrs = d["years"]

    # Build chart-ready series
    trend_series = [
        {"year": y, "count": d["annual_totals"][y], "series": "All Centres"}
        for y in yrs
    ]
    lfl_series = [
        {"year": y, "count": d["lfl_annual"][y], "series": "Like-for-Like (3 centres)"}
        for y in yrs
    ]

    # YoY table
    yoy_table = [
        {
            "year": yrs[i],
            "count": d["annual_totals"][yrs[i]],
            "yoy_pct": d["yoy_pct"].get(yrs[i]),
            "lfl_count": d["lfl_annual"].get(yrs[i]),
            "lfl_yoy_pct": d["lfl_yoy_pct"].get(yrs[i]),
            "n_reporting": sum(
                1 for c in d["centres"]
                if c.get(yrs[i]) is not None
            ),
        }
        for i in range(len(yrs))
    ]

    return {
        "available": True,
        "trend_series": trend_series + lfl_series,
        "yoy_table": yoy_table,
        "lfl_centres": d["lfl_centres"],
        "partner_totals": d["partner_totals"],
        "coverage": d["coverage"],
        "grand_total": d["grand_total"],
        "totals_match": d["totals_match"],
    }


def gttc_centres() -> dict:
    """Return per-centre data for bar charts and tables."""
    d = load_gttc_courses()
    if not d.get("available"):
        return d

    yrs = d["years"]

    # Sorted by total descending
    centres_sorted = sorted(d["centres"], key=lambda x: (x.get("total") or 0), reverse=True)

    # Concentration indicator
    totals_sorted = sorted(
        [(c["centre"], c.get("total") or 0) for c in d["centres"]],
        key=lambda x: -x[1]
    )
    grand = d["grand_total"]
    cumulative = 0
    concentration = []
    for name, total in totals_sorted:
        cumulative += total
        concentration.append({
            "centre": name,
            "total": total,
            "share_pct": round(total / grand * 100, 2) if grand else 0,
            "cumulative_pct": round(cumulative / grand * 100, 2) if grand else 0,
        })

    # Partner breakdown
    partner_list = [
        {"partner": k, "total": int(v), "share_pct": round(int(v) / grand * 100, 2)}
        for k, v in d["partner_totals"].items()
    ]
    partner_list.sort(key=lambda x: -x["total"])

    return {
        "available": True,
        "centres": centres_sorted,
        "concentration": concentration,
        "partner_breakdown": partner_list,
        "years": yrs,
        "grand_total": grand,
    }


def gttc_coverage() -> dict:
    """Return data-quality / coverage detail for GTTC files."""
    d = load_gttc_courses()
    p = load_gttc_passed()

    result = {"available": d.get("available")}

    if d.get("available"):
        yrs = d["years"]
        # Per-year reporting counts
        reporting = [
            {
                "year": y,
                "reporting_centres": sum(1 for c in d["centres"] if c.get(y) is not None),
                "total_centres": len(d["centres"]),
            }
            for y in yrs
        ]
        result.update({
            "coverage": d["coverage"],
            "reporting_by_year": reporting,
            "lfl_centres": d["lfl_centres"],
            "totals_match": d["totals_match"],
        })

    if p.get("available"):
        result["passed_coe"] = p.get("coe_counts", {})
        result["passed_short_term"] = p.get("short_term_counts", {})
        result["manufacturing_order"] = p.get("manufacturing_order_value", {})
        result["center_counts"] = p.get("center_counts", {})
        result["all_programmes"] = p.get("programmes", [])

    return result


def census_industry() -> dict:
    """Return industry-level breakdown of Census marginal workers."""
    d = load_census()
    if not d.get("available"):
        return d

    return {
        "available": True,
        "total_persons": d["total_persons"],
        "categories": d["categories"],
        "agri_persons": d["agri_persons"],
        "agri_share_pct": d["agri_share_pct"],
        "rural_total": d["rural_total"],
        "urban_total": d["urban_total"],
    }


def census_demographics() -> dict:
    """Return gender and age breakdowns from Census data."""
    d = load_census()
    if not d.get("available"):
        return d

    return {
        "available": True,
        "total_persons": d["total_persons"],
        "total_males": d["total_males"],
        "total_females": d["total_females"],
        "female_share_pct": d["female_share_pct"],
        "age_breakdown": d["age_breakdown"],
        "districts": d["districts"],
        "n_districts": d["n_districts"],
    }


def enrolment_overview() -> dict:
    """Return school enrolment overview from both enrolment files."""
    e21 = load_enrolment_2021()
    result = {
        "enrolment_2021": e21,
        "note": (
            "School enrolment data is contextual — it represents the wider education "
            "pipeline, not vocational training capacity, job readiness, or employability."
        ),
    }
    return result


def industry_overview() -> dict:
    """Return SLSWCC industry signals."""
    d = load_slswcc()
    if not d.get("available"):
        return d

    return {
        "available": True,
        "n_units": d["n_units"],
        "total_employment": d["total_employment"],
        "total_investment": d["total_investment"],
        "zero_employment_units": d["zero_employment_units"],
        "sectors": d["sectors"],
        "district_employment": d["district_employment"],
        "investment_stats": d["investment_stats"],
        "clean_sector_count": d["clean_sector_count"],
        "district_parsed_count": d["district_parsed_count"],
        "limitation": (
            "Figures represent approved-project or listed employment at the time of "
            "single-window approval. They are not verified realised jobs or current vacancies."
        ),
    }


def methodology_indicators() -> list:
    """Return indicator definitions for the methodology section."""
    return [
        {
            "id": "I1",
            "name": "Annual Reported Training Activity",
            "formula": "A(t) = Σ centre counts in year t",
            "level": "Centre × Financial Year",
            "informs": "Track reported CoE volume over time",
            "cannot_establish": "Demand, completion, placement or training quality",
            "status": "Implemented",
            "prototype_value": "1,040 → 2,420 (FY 2018–19 to 2021–22)",
        },
        {
            "id": "I2",
            "name": "Year-over-Year Change",
            "formula": "[A(t) − A(t−1)] ÷ A(t−1) × 100",
            "level": "State / Centre × Financial Year",
            "informs": "Review centres with volatile reported throughput",
            "cannot_establish": "Why counts changed (e.g. policy, COVID-19 timing, reporting method)",
            "status": "Implemented",
            "prototype_value": "+141.8% / −17.1% / +16.0%",
        },
        {
            "id": "I3",
            "name": "Centre Concentration",
            "formula": "Share(c) = N(c) ÷ ΣN",
            "level": "Centre × Period",
            "informs": "Check regional spread of CoE activity",
            "cannot_establish": "Whether spread matches training need or demand",
            "status": "Implemented",
            "prototype_value": "Mysuru 34.6%; top-two centres 59.7%",
        },
        {
            "id": "I4",
            "name": "Completion / Pass Rate",
            "formula": "Passed ÷ Enrolled (same course, centre, year)",
            "level": "Course × Centre × Year",
            "informs": "Spot courses with low reported completion",
            "cannot_establish": "Employment outcomes; quality; reasons for non-completion",
            "status": "Not Computable",
            "prototype_value": "No denominator (enrolment by course) in available files",
        },
        {
            "id": "I5",
            "name": "Potential Alignment Flag",
            "formula": (
                "Flag when a sector's employment-signal share is high "
                "and its mapped training share is low. Requires trade→sector map."
            ),
            "level": "District × Sector × Period",
            "informs": "Choose where to investigate with employers",
            "cannot_establish": "Skill shortage, vacancy, or causal relationship",
            "status": "Proposed",
            "prototype_value": "Requires district crosswalk and trade-sector map not yet built",
        },
        {
            "id": "I6",
            "name": "Completeness and Freshness",
            "formula": "Filled cells ÷ Expected cells; latest period per source",
            "level": "Dataset",
            "informs": "Decide if an indicator is safe to use",
            "cannot_establish": "Correctness of filled values",
            "status": "Implemented",
            "prototype_value": "GTTC file: 23 of 40 cells filled (57.5%)",
        },
    ]
