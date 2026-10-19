"""
data_loader.py
Loads and validates each raw CSV exactly as uploaded. Raw files are never modified.
All paths are resolved relative to DATA_DIR (configurable via environment variable).
"""

import os
import re
import pandas as pd
import numpy as np
from pathlib import Path

# ── Data directory ─────────────────────────────────────────────────────────────
# Default: <project_root>/data/  (sits next to backend/ and frontend/)
_default_data_dir = Path(__file__).resolve().parent.parent / "data"
DATA_DIR = Path(os.environ.get("DATA_DIR", str(_default_data_dir)))

# ── File-name registry ─────────────────────────────────────────────────────────
FILES = {
    "gttc_courses":   "GTTC_Shortterm_Courses.csv",
    "gttc_passed":    "GTTC_Number_of_Students_Passed_2019-2021_0.csv",
    "census":         "census_2011_ddw_b06_2900_2011.csv",
    "enrolment_2021": "TotalEnrollmentbyLevel_2020-21.csv",
    "enrolment_2019": "ManagementWiseClasswiseEnrolment2018_2019_1.csv",
    "slswcc":         "State_Level_Single_Window_Committee_Industrydetails_2021.csv",
}


def _path(key: str) -> Path:
    return DATA_DIR / FILES[key]


def _available(key: str) -> bool:
    return _path(key).exists()


# ── Loaders ────────────────────────────────────────────────────────────────────

def load_gttc_courses() -> dict:
    """Load and validate GTTC short-term CoE courses file."""
    key = "gttc_courses"
    if not _available(key):
        return {"available": False, "file": FILES[key]}

    df = pd.read_csv(_path(key))
    yrs = ["2018-19", "2019-20", "2020-21", "2021-22"]

    # Forward-fill CoE column
    df["CoE"] = df["Centre of Excellence"].ffill()

    # Separate data rows from totals row
    data = df[df["Sl.No"].astype(str).str.strip().str.isnumeric()].copy()
    total_row = df[df["Sl.No"].astype(str).str.strip() == "Total"]

    for y in yrs + ["Total"]:
        data[y] = pd.to_numeric(data[y], errors="coerce")

    file_totals = {}
    if len(total_row):
        tr = total_row.iloc[0]
        for y in yrs + ["Total"]:
            try:
                file_totals[y] = int(tr[y])
            except Exception:
                file_totals[y] = None

    computed_totals = {y: int(data[y].sum()) for y in yrs}
    computed_grand  = int(data["Total"].sum())

    # LFL cohort: centres with data in all 4 years
    lfl = data[data[yrs].notna().all(axis=1)]

    # YoY
    t = computed_totals
    yoy = {}
    for i in range(1, len(yrs)):
        prev = t[yrs[i - 1]]
        if prev:
            yoy[yrs[i]] = round((t[yrs[i]] - prev) / prev * 100, 2)

    lfl_totals = {y: int(lfl[y].sum()) for y in yrs}
    lfl_yoy = {}
    for i in range(1, len(yrs)):
        prev = lfl_totals[yrs[i - 1]]
        if prev:
            lfl_yoy[yrs[i]] = round((lfl_totals[yrs[i]] - prev) / prev * 100, 2)

    # Partner breakdown
    partner = data.groupby("CoE")["Total"].sum().to_dict()

    # Coverage
    filled = int(data[yrs].notna().sum().sum())
    cells  = int(data[yrs].size)

    # Centres table
    centres_list = []
    for _, row in data.iterrows():
        entry = {
            "centre": row["Centre Name"],
            "coe": row["CoE"],
            "total": int(row["Total"]) if pd.notna(row["Total"]) else None,
        }
        for y in yrs:
            entry[y] = int(row[y]) if pd.notna(row[y]) else None
        centres_list.append(entry)

    return {
        "available": True,
        "file": FILES[key],
        "years": yrs,
        "annual_totals": computed_totals,
        "file_totals": file_totals,
        "grand_total": computed_grand,
        "yoy_pct": yoy,
        "lfl_centres": lfl["Centre Name"].tolist(),
        "lfl_annual": lfl_totals,
        "lfl_yoy_pct": lfl_yoy,
        "partner_totals": partner,
        "centres": centres_list,
        "coverage": {"filled": filled, "cells": cells, "pct": round(filled / cells * 100, 1)},
        "totals_match": (computed_totals == {y: file_totals.get(y) for y in yrs}),
    }


def load_gttc_passed() -> dict:
    """Load GTTC students-passed file."""
    key = "gttc_passed"
    if not _available(key):
        return {"available": False, "file": FILES[key]}

    df = pd.read_csv(_path(key), keep_default_na=False)
    years = ["2019", "2020", "2021"]
    passed_cols = [c for c in df.columns if "PASSED OUT" in c.upper()]
    order_cols  = [c for c in df.columns if "ORDER VALUE" in c.upper()]
    center_cols = [c for c in df.columns if "NO OF CENTER" in c.upper()]

    programmes = []
    for _, row in df.iterrows():
        info_type = str(row["INFORMATION TYPE"]).strip()
        entry = {"programme": info_type}
        for col in passed_cols:
            yr = re.search(r"20\d\d", col)
            if yr:
                raw = str(row[col]).strip()
                entry[f"passed_{yr.group()}"] = (
                    int(raw) if raw.lstrip("-").isdigit() else raw
                )
        for col in order_cols:
            yr = re.search(r"20\d\d", col)
            if yr:
                raw = str(row[col]).strip()
                try:
                    entry[f"order_value_{yr.group()}"] = float(raw)
                except ValueError:
                    entry[f"order_value_{yr.group()}"] = None
        for col in center_cols:
            yr = re.search(r"20\d\d", col)
            if yr:
                raw = str(row[col]).strip()
                try:
                    entry[f"centers_{yr.group()}"] = int(raw)
                except ValueError:
                    entry[f"centers_{yr.group()}"] = None
        programmes.append(entry)

    # Pull specific rows
    def _get_row(keyword):
        rows = [p for p in programmes if keyword.upper() in p["programme"].upper()]
        return rows[0] if rows else None

    coe_row     = _get_row("COE")
    short_row   = _get_row("SHORT TERM")
    mfg_row     = _get_row("MANUFACTRING")
    centers_row = _get_row("NO OF GTTC")

    def _int_or_none(val):
        try:
            return int(val)
        except (TypeError, ValueError):
            return None

    return {
        "available": True,
        "file": FILES[key],
        "programmes": programmes,
        "coe_counts": {y: _int_or_none(coe_row.get(f"passed_{y}")) for y in years} if coe_row else {},
        "short_term_counts": {y: _int_or_none(short_row.get(f"passed_{y}")) for y in years} if short_row else {},
        "manufacturing_order_value": {
            y: mfg_row.get(f"order_value_{y}") for y in years
        } if mfg_row else {},
        "center_counts": {
            y: centers_row.get(f"centers_{y}") for y in years
        } if centers_row else {},
    }


def load_census() -> dict:
    """Load Census 2011 Table B-06 marginal workers file."""
    key = "census"
    if not _available(key):
        return {"available": False, "file": FILES[key]}

    df = pd.read_csv(_path(key))
    df["Area Name"] = df["Area Name"].str.strip()

    # Industry category columns (Persons)
    ind_cols_p = [c for c in df.columns if c.startswith("Industrial Category") and c.endswith("Persons")]
    ind_cols_m = [c for c in df.columns if c.startswith("Industrial Category") and c.endswith("Males")]
    ind_cols_f = [c for c in df.columns if c.startswith("Industrial Category") and c.endswith("Females")]

    # State-level, Total/Total row
    mask = (
        (df["Area Name"] == "State - Karnataka") &
        (df["Total/Rural/Urban"] == "Total") &
        (df["Age-Group"] == "Total")
    )
    state_row = df[mask].iloc[0]

    total_persons = int(state_row[ind_cols_p].sum())
    total_males   = int(state_row[ind_cols_m].sum())
    total_females = int(state_row[ind_cols_f].sum())

    # Build category breakdown
    # Map internal category codes to readable labels
    CAT_LABELS = {
        "A": "Agriculture, Forestry & Fishing",
        "B": "Mining & Quarrying",
        "C": "Manufacturing",
        "D & E": "Electricity, Gas & Water",
        "F": "Construction",
        "G": "Trade & Repair",
        "H": "Hotels & Restaurants",
        "I": "Transport, Storage & Communication",
        "J": "Finance & Insurance",
        "K to M": "Real Estate & Business",
        "N to O": "Public Admin & Defence",
        "P to Q": "Education & Health",
        "R to U": "Other Services",
    }

    categories = []
    for code, label in CAT_LABELS.items():
        p_cols = [c for c in ind_cols_p if f"- {code} -" in c or c == f"Industrial Category - {code} - Persons" or (f" {code} - " not in c and c == f"Industrial Category - {code} - Persons")]
        # More robust: match columns containing " - {code}" pattern
        p_match = [c for c in ind_cols_p if re.search(r' - ' + re.escape(code) + r'( |$| -)', c)]
        m_match = [c for c in ind_cols_m if re.search(r' - ' + re.escape(code) + r'( |$| -)', c)]
        f_match = [c for c in ind_cols_f if re.search(r' - ' + re.escape(code) + r'( |$| -)', c)]

        p_val = int(state_row[p_match].sum()) if p_match else 0
        m_val = int(state_row[m_match].sum()) if m_match else 0
        f_val = int(state_row[f_match].sum()) if f_match else 0

        if p_val > 0:
            categories.append({
                "code": code,
                "label": label,
                "persons": p_val,
                "males": m_val,
                "females": f_val,
                "share_pct": round(p_val / total_persons * 100, 2) if total_persons else 0,
            })

    # Agri share
    agri_cols = [c for c in ind_cols_p if " - A - " in c]
    agri_total = int(state_row[agri_cols].sum())

    # Rural/Urban split
    rural_mask = (
        (df["Area Name"] == "State - Karnataka") &
        (df["Total/Rural/Urban"] == "Rural") &
        (df["Age-Group"] == "Total")
    )
    urban_mask = (
        (df["Area Name"] == "State - Karnataka") &
        (df["Total/Rural/Urban"] == "Urban") &
        (df["Age-Group"] == "Total")
    )
    rural_row = df[rural_mask].iloc[0] if df[rural_mask].any().any() else None
    urban_row = df[urban_mask].iloc[0] if df[urban_mask].any().any() else None

    rural_total = int(df[rural_mask].iloc[0][ind_cols_p].sum()) if len(df[rural_mask]) else 0
    urban_total = int(df[urban_mask].iloc[0][ind_cols_p].sum()) if len(df[urban_mask]) else 0

    # Age group breakdown for state
    age_rows = df[
        (df["Area Name"] == "State - Karnataka") &
        (df["Total/Rural/Urban"] == "Total") &
        (df["Age-Group"] != "Total")
    ].copy()
    age_breakdown = []
    for _, row in age_rows.iterrows():
        p = int(row[ind_cols_p].sum())
        m = int(row[ind_cols_m].sum())
        f = int(row[ind_cols_f].sum())
        age_breakdown.append({
            "age_group": row["Age-Group"],
            "persons": p, "males": m, "females": f,
        })

    # District-level totals
    district_rows = df[
        (df["Area Name"].str.startswith("District")) &
        (df["Total/Rural/Urban"] == "Total") &
        (df["Age-Group"] == "Total")
    ].copy()
    districts = []
    for _, row in district_rows.iterrows():
        p = int(row[ind_cols_p].sum())
        districts.append({
            "district": row["Area Name"].replace("District - ", ""),
            "persons": p,
        })
    districts.sort(key=lambda x: -x["persons"])

    return {
        "available": True,
        "file": FILES[key],
        "total_persons": total_persons,
        "total_males": total_males,
        "total_females": total_females,
        "agri_persons": agri_total,
        "agri_share_pct": round(agri_total / total_persons * 100, 2) if total_persons else 0,
        "female_share_pct": round(total_females / total_persons * 100, 2) if total_persons else 0,
        "rural_total": rural_total,
        "urban_total": urban_total,
        "categories": sorted(categories, key=lambda x: -x["persons"]),
        "age_breakdown": age_breakdown,
        "districts": districts,
        "n_districts": len(districts),
    }


def load_enrolment_2021() -> dict:
    """Load Total Enrolment by Level 2020-21."""
    key = "enrolment_2021"
    if not _available(key):
        return {"available": False, "file": FILES[key]}

    df = pd.read_csv(_path(key))
    df.columns = [x.strip() for x in df.columns]

    # Find corrupted cell and flag it
    corrupted = []
    for col in df.columns:
        for idx, val in df[col].items():
            if isinstance(val, str) and "%" in str(val):
                corrupted.append({"row": int(idx), "col": col, "raw": val})

    # All Management rows only
    am = df[df["Management"].str.contains("All Management", na=False)]
    districts = [r for r in am["District"].dropna().tolist() if str(r).strip()]

    # Level columns: look for Class 1 to 12 total
    total_col = [c for c in df.columns if "Class 1 and 12" in c or "Class 1 to 12" in c]
    boys_col = [c for c in df.columns if "Class 1 and 12 Boys" in c]
    girls_col = [c for c in df.columns if "Class 1 and 12 Girls" in c]

    # Build district summary
    district_data = []
    for _, row in am.iterrows():
        dist = str(row.get("District", "")).strip()
        if not dist or dist.lower() in ("nan", ""):
            continue
        entry = {"district": dist}
        for lbl, cols in [
            ("pre_primary", [c for c in df.columns if "Pre Primary" in c and "Total" in c and "Boys" not in c and "Girls" not in c]),
            ("class_1_8", [c for c in df.columns if "Class 1 to 8" in c and "Total" in c]),
            ("class_9_10", [c for c in df.columns if "Class 9 and 10" in c and "Total" in c]),
            ("class_11_12", [c for c in df.columns if "Class 11 and 12" in c and "Total" in c]),
        ]:
            val = None
            for col in cols:
                v = row.get(col)
                if v is not None and str(v).strip() not in ("nan", ""):
                    try:
                        val = int(float(str(v).replace(",", "").replace("%", "")))
                        break
                    except Exception:
                        pass
            entry[lbl] = val
        district_data.append(entry)

    return {
        "available": True,
        "file": FILES[key],
        "n_districts": len(districts),
        "districts": district_data,
        "corrupted_cells": corrupted,
        "management_types": df["Management"].dropna().unique().tolist(),
    }


def load_slswcc() -> dict:
    """Load Single Window Committee industry details 2021."""
    key = "slswcc"
    if not _available(key):
        return {"available": False, "file": FILES[key]}

    df = pd.read_csv(_path(key), encoding="cp1252")
    df.columns = [c.replace("\n", " ").strip() for c in df.columns]

    # Clean sector labels
    df["SECTOR_CLEAN"] = df["SECTOR"].str.strip().str.upper()

    n_units      = len(df)
    total_emp    = int(df["EMPLOYMENT"].sum())
    total_inv    = round(float(df["INVESTMENT (Rs. In Crores)"].sum()), 2)
    zero_emp     = int((df["EMPLOYMENT"] == 0).sum())
    raw_sectors  = int(df["SECTOR"].nunique())
    clean_sectors = int(df["SECTOR_CLEAN"].nunique())

    # Sector breakdown
    sector_grp = df.groupby("SECTOR_CLEAN").agg(
        units=("SECTOR_CLEAN", "count"),
        employment=("EMPLOYMENT", "sum"),
        investment=("INVESTMENT (Rs. In Crores)", "sum"),
    ).reset_index()
    sector_grp["employment"] = sector_grp["employment"].astype(int)
    sector_grp["investment"] = sector_grp["investment"].round(2)
    sector_list = sector_grp.sort_values("employment", ascending=False).to_dict(orient="records")

    # District parsing
    def _dist(x):
        m = re.search(r"([A-Za-z\.\s]+?)\s+Dist", str(x))
        return m.group(1).strip() if m else None

    df["parsed_dist"] = df["LOCATION"].map(_dist)
    dist_parsed = int(df["parsed_dist"].notna().sum())

    dist_emp = (
        df[df["parsed_dist"].notna()]
        .groupby("parsed_dist")["EMPLOYMENT"].sum()
        .sort_values(ascending=False)
        .head(20)
        .to_dict()
    )

    # Investment range
    inv_stats = {
        "min": round(float(df["INVESTMENT (Rs. In Crores)"].min()), 2),
        "max": round(float(df["INVESTMENT (Rs. In Crores)"].max()), 2),
        "mean": round(float(df["INVESTMENT (Rs. In Crores)"].mean()), 2),
        "median": round(float(df["INVESTMENT (Rs. In Crores)"].median()), 2),
    }

    return {
        "available": True,
        "file": FILES[key],
        "n_units": n_units,
        "total_employment": total_emp,
        "total_investment": total_inv,
        "zero_employment_units": zero_emp,
        "raw_sector_count": raw_sectors,
        "clean_sector_count": clean_sectors,
        "sectors": sector_list,
        "district_parsed_count": dist_parsed,
        "district_employment": dist_emp,
        "investment_stats": inv_stats,
    }


def load_enrolment_2019() -> dict:
    """Load Management-wise Class-wise Enrolment 2018-19."""
    key = "enrolment_2019"
    if not _available(key):
        return {"available": False, "file": FILES[key]}

    df = pd.read_csv(_path(key))

    # All Category + All Management equivalent
    all_cat = df[df["Social Category"].astype(str).str.contains("All Category", na=False)]

    # Find total-enrolment column
    total_cols = [c for c in df.columns if "Total Class 1 to 12" in c and "Boys" not in c and "Girls" not in c]
    boys_cols  = [c for c in df.columns if "Total Class 1 to 12 Boys" in c]
    girls_cols = [c for c in df.columns if "Total Class 1 to 12 Girls" in c]

    management_types = df["Management"].dropna().unique().tolist()
    district_list = all_cat["District"].dropna().unique().tolist()

    return {
        "available": True,
        "file": FILES[key],
        "n_rows": len(df),
        "management_types": management_types,
        "n_districts": len(district_list),
        "note": "Contains LKG to Class 12 enrolment by district, management and social category for AY 2018-19.",
    }


# ── Convenience: load everything ─────────────────────────────────────────────

def load_all() -> dict:
    return {
        "gttc_courses":   load_gttc_courses(),
        "gttc_passed":    load_gttc_passed(),
        "census":         load_census(),
        "enrolment_2021": load_enrolment_2021(),
        "enrolment_2019": load_enrolment_2019(),
        "slswcc":         load_slswcc(),
    }


def dataset_status() -> list:
    """Return availability status for every expected dataset."""
    statuses = []
    labels = {
        "gttc_courses":   ("GTTC Short-term Courses", "FY 2018–19 to 2021–22"),
        "gttc_passed":    ("GTTC Students Passed 2019–2021", "Calendar 2019–2021"),
        "census":         ("Census 2011 Table B-06", "2011"),
        "enrolment_2021": ("Total Enrolment by Level 2020–21", "AY 2020–21"),
        "enrolment_2019": ("Management-wise Enrolment 2018–19", "AY 2018–19"),
        "slswcc":         ("Single Window Committee 2021", "FY 2020–21"),
    }
    for key, (label, period) in labels.items():
        statuses.append({
            "key": key,
            "label": label,
            "period": period,
            "file": FILES[key],
            "available": _available(key),
        })
    return statuses
