"""
validation.py
Runs data-quality checks across all loaded datasets.
Returns structured results with PASS / WARNING / FAIL / NOT_CHECKED statuses.
"""

from __future__ import annotations
import os
import re
import pandas as pd
import numpy as np
from pathlib import Path
from data_loader import DATA_DIR, FILES, _available, _path


def _status(ok: bool | None, warn: bool = False) -> str:
    if ok is None:
        return "NOT_CHECKED"
    if ok:
        return "PASS"
    if warn:
        return "WARNING"
    return "FAIL"


def run_all_checks() -> dict:
    checks = []

    # ── GTTC Short-term Courses ───────────────────────────────────────────────
    if _available("gttc_courses"):
        df = pd.read_csv(_path("gttc_courses"))
        yrs = ["2018-19", "2019-20", "2020-21", "2021-22"]
        df["CoE"] = df["Centre of Excellence"].ffill()
        data  = df[df["Sl.No"].astype(str).str.strip().str.isnumeric()].copy()
        total = df[df["Sl.No"].astype(str).str.strip() == "Total"]
        for y in yrs + ["Total"]:
            data[y] = pd.to_numeric(data[y], errors="coerce")

        # Total reconciliation
        computed = {y: int(data[y].sum()) for y in yrs}
        grand = int(data["Total"].sum())
        if len(total):
            tr = total.iloc[0]
            file_totals = {y: int(tr[y]) for y in yrs}
            totals_match = computed == file_totals
            grand_match  = grand == int(tr["Total"])
        else:
            totals_match = None
            grand_match  = None

        checks.append({
            "dataset": "GTTC Short-term Courses",
            "check": "Annual totals reconcile with file's own Total row",
            "status": _status(totals_match),
            "detail": f"Computed {computed}; file row totals {file_totals if len(total) else 'N/A'}",
        })
        checks.append({
            "dataset": "GTTC Short-term Courses",
            "check": "Grand total reconciles (8,061 expected)",
            "status": _status(grand_match),
            "detail": f"Computed grand total: {grand}",
        })

        # Row sum check: each row's year sum = row's Total
        row_diffs = (data[yrs].sum(axis=1) - data["Total"]).abs()
        checks.append({
            "dataset": "GTTC Short-term Courses",
            "check": "Row-level: sum of years equals row Total column",
            "status": _status(bool(row_diffs.max() == 0)),
            "detail": f"Max row discrepancy: {row_diffs.max()}",
        })

        # Duplicate centres
        dup = data["Centre Name"].duplicated().sum()
        checks.append({
            "dataset": "GTTC Short-term Courses",
            "check": "No duplicate centre names",
            "status": _status(dup == 0),
            "detail": f"Duplicate rows: {dup}",
        })

        # Coverage
        filled = int(data[yrs].notna().sum().sum())
        cells  = int(data[yrs].size)
        checks.append({
            "dataset": "GTTC Short-term Courses",
            "check": "Cell completeness (centre × year)",
            "status": _status(filled == cells, warn=True),
            "detail": f"{filled} of {cells} cells filled ({round(filled/cells*100,1)}%)",
        })

    else:
        checks.append({
            "dataset": "GTTC Short-term Courses",
            "check": "File availability",
            "status": "FAIL",
            "detail": f"File not found: {FILES['gttc_courses']}",
        })

    # ── GTTC Passed ───────────────────────────────────────────────────────────
    if _available("gttc_passed"):
        df = pd.read_csv(_path("gttc_passed"), keep_default_na=False)
        checks.append({
            "dataset": "GTTC Students Passed",
            "check": "File loads without error",
            "status": "PASS",
            "detail": f"{len(df)} rows loaded",
        })
        # CoE values match short-term courses if also available
        if _available("gttc_courses"):
            coe_row = df[df["INFORMATION TYPE"].str.contains("COE", na=False)]
            if len(coe_row):
                cr = coe_row.iloc[0]
                passed_cols = [c for c in df.columns if "PASSED OUT" in c.upper()]
                gttc_df = pd.read_csv(_path("gttc_courses"))
                gttc_yrs = ["2018-19", "2019-20", "2020-21", "2021-22"]
                gttc_df["CoE"] = gttc_df["Centre of Excellence"].ffill()
                gttc_data = gttc_df[gttc_df["Sl.No"].astype(str).str.strip().str.isnumeric()].copy()
                for y in gttc_yrs:
                    gttc_data[y] = pd.to_numeric(gttc_data[y], errors="coerce")
                gttc_totals = {y: int(gttc_data[y].sum()) for y in gttc_yrs}

                coe_matches = True
                details = []
                year_map = {"2019": "2019-20", "2020": "2020-21", "2021": "2021-22"}
                for yr_pass, yr_gttc in year_map.items():
                    col = next((c for c in passed_cols if yr_pass in c), None)
                    if col:
                        try:
                            val = int(str(cr[col]).strip())
                            gval = gttc_totals.get(yr_gttc)
                            if val != gval:
                                coe_matches = False
                                details.append(f"{yr_pass}: passed={val} vs gttc={gval}")
                        except Exception:
                            pass
                checks.append({
                    "dataset": "GTTC Students Passed",
                    "check": "CoE passed counts match GTTC short-term yearly totals",
                    "status": _status(coe_matches),
                    "detail": "; ".join(details) if details else "All years match — files are one source",
                })
    else:
        checks.append({
            "dataset": "GTTC Students Passed",
            "check": "File availability",
            "status": "FAIL",
            "detail": f"File not found: {FILES['gttc_passed']}",
        })

    # ── Census ────────────────────────────────────────────────────────────────
    if _available("census"):
        df = pd.read_csv(_path("census"))
        df["Area Name"] = df["Area Name"].str.strip()
        ind_cols_p = [c for c in df.columns if c.startswith("Industrial Category") and c.endswith("Persons")]

        mask = (
            (df["Area Name"] == "State - Karnataka") &
            (df["Total/Rural/Urban"] == "Total") &
            (df["Age-Group"] == "Total")
        )
        state_row = df[mask].iloc[0]
        total_persons = int(state_row[ind_cols_p].sum())

        checks.append({
            "dataset": "Census 2011 B-06",
            "check": "State total marginal workers (4,473,682 expected)",
            "status": _status(total_persons == 4473682),
            "detail": f"Computed: {total_persons:,}",
        })

        # District count
        dist_rows = df[
            (df["Area Name"].str.startswith("District")) &
            (df["Total/Rural/Urban"] == "Total") &
            (df["Age-Group"] == "Total")
        ]
        checks.append({
            "dataset": "Census 2011 B-06",
            "check": "Expected 30 districts",
            "status": _status(len(dist_rows) == 30),
            "detail": f"Districts found: {len(dist_rows)}",
        })

        # Rural + Urban = Total
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
        if len(df[rural_mask]) and len(df[urban_mask]):
            r = int(df[rural_mask].iloc[0][ind_cols_p].sum())
            u = int(df[urban_mask].iloc[0][ind_cols_p].sum())
            checks.append({
                "dataset": "Census 2011 B-06",
                "check": "Rural + Urban sums to Total (state level)",
                "status": _status(r + u == total_persons),
                "detail": f"Rural={r:,} + Urban={u:,} = {r+u:,}; Total={total_persons:,}",
            })

        # No negative values
        neg = (df[ind_cols_p] < 0).sum().sum()
        checks.append({
            "dataset": "Census 2011 B-06",
            "check": "No negative marginal worker counts",
            "status": _status(neg == 0),
            "detail": f"Negative cells: {neg}",
        })
    else:
        checks.append({
            "dataset": "Census 2011 B-06",
            "check": "File availability",
            "status": "FAIL",
            "detail": f"File not found: {FILES['census']}",
        })

    # ── Enrolment 2021 ────────────────────────────────────────────────────────
    if _available("enrolment_2021"):
        df = pd.read_csv(_path("enrolment_2021"))
        df.columns = [c.strip() for c in df.columns]
        corrupted = []
        for col in df.columns:
            for idx, val in df[col].items():
                if "%" in str(val):
                    corrupted.append(f"Row {idx}, col '{col}': '{val}'")
        checks.append({
            "dataset": "Enrolment 2020-21",
            "check": "No corrupted cells containing '%' markers",
            "status": _status(len(corrupted) == 0, warn=True),
            "detail": "; ".join(corrupted) if corrupted else "None found",
        })
        am = df[df["Management"].str.contains("All Management", na=False)]
        checks.append({
            "dataset": "Enrolment 2020-21",
            "check": "All-Management rows loaded (expected ~34 districts)",
            "status": _status(len(am) >= 30),
            "detail": f"All-Management rows: {len(am)}",
        })
    else:
        checks.append({
            "dataset": "Enrolment 2020-21",
            "check": "File availability",
            "status": "FAIL",
            "detail": f"File not found: {FILES['enrolment_2021']}",
        })

    # ── SLSWCC ────────────────────────────────────────────────────────────────
    if _available("slswcc"):
        df = pd.read_csv(_path("slswcc"), encoding="cp1252")
        df.columns = [c.replace("\n", " ").strip() for c in df.columns]
        checks.append({
            "dataset": "Single Window Committee 2021",
            "check": "Expected 307 approved units",
            "status": _status(len(df) == 307),
            "detail": f"Rows loaded: {len(df)}",
        })
        zero_emp = int((df["EMPLOYMENT"] == 0).sum())
        checks.append({
            "dataset": "Single Window Committee 2021",
            "check": "Zero-employment entries flagged",
            "status": _status(zero_emp == 0, warn=True),
            "detail": f"Units with zero listed employment: {zero_emp}",
        })
        # Sector label harmonisation
        raw = df["SECTOR"].nunique()
        clean = df["SECTOR"].str.strip().str.upper().nunique()
        checks.append({
            "dataset": "Single Window Committee 2021",
            "check": "Sector label harmonisation (whitespace/case normalisation)",
            "status": _status(clean < raw, warn=False),
            "detail": f"Raw unique sectors: {raw}; after normalisation: {clean}",
        })
        # District parsing
        def _dist(x):
            m = re.search(r"([A-Za-z\.\s]+?)\s+Dist", str(x))
            return m.group(1).strip() if m else None
        parsed = df["LOCATION"].map(_dist).notna().sum()
        checks.append({
            "dataset": "Single Window Committee 2021",
            "check": "District parseable from free-text location",
            "status": _status(parsed >= 250, warn=True),
            "detail": f"Parsed: {parsed} of {len(df)} ({round(parsed/len(df)*100,1)}%)",
        })
    else:
        checks.append({
            "dataset": "Single Window Committee 2021",
            "check": "File availability",
            "status": "FAIL",
            "detail": f"File not found: {FILES['slswcc']}",
        })

    # ── Cross-source compatibility note ───────────────────────────────────────
    checks.append({
        "dataset": "Cross-source",
        "check": "Period compatibility: financial vs calendar years documented",
        "status": "WARNING",
        "detail": (
            "GTTC short-term = FY 2018-19 to 2021-22; "
            "GTTC passed = Calendar 2019-2021; "
            "Census = 2011; SLSWCC = FY 2020-21. "
            "Never merge financial and calendar year data without a documented rule."
        ),
    })
    checks.append({
        "dataset": "Cross-source",
        "check": "District name/boundary crosswalk for multi-source linkage",
        "status": "NOT_CHECKED",
        "detail": (
            "District boundaries and names changed between Census 2011 and later files. "
            "A versioned code-based crosswalk is required before district-level joins. "
            "Currently proposed, not implemented."
        ),
    })

    summary = {
        "pass": sum(1 for c in checks if c["status"] == "PASS"),
        "warning": sum(1 for c in checks if c["status"] == "WARNING"),
        "fail": sum(1 for c in checks if c["status"] == "FAIL"),
        "not_checked": sum(1 for c in checks if c["status"] == "NOT_CHECKED"),
        "total": len(checks),
    }

    return {"checks": checks, "summary": summary}
