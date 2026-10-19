"""
Tests for core analytics and data loading.
Run: python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from data_loader import (
    load_gttc_courses, load_gttc_passed, load_census,
    load_enrolment_2021, load_slswcc, dataset_status
)
from analytics import gttc_trends, gttc_centres, census_industry
from validation import run_all_checks


# ── Dataset availability ───────────────────────────────────────────────────────

def test_all_datasets_available():
    statuses = dataset_status()
    unavailable = [s for s in statuses if not s["available"]]
    assert unavailable == [], f"Missing datasets: {[s['file'] for s in unavailable]}"


# ── GTTC Short-term Courses ───────────────────────────────────────────────────

def test_gttc_grand_total():
    d = load_gttc_courses()
    assert d["available"], "GTTC courses file not available"
    assert d["grand_total"] == 8061, f"Expected 8061, got {d['grand_total']}"


def test_gttc_annual_totals():
    d = load_gttc_courses()
    assert d["available"]
    expected = {"2018-19": 1040, "2019-20": 2515, "2020-21": 2086, "2021-22": 2420}
    assert d["annual_totals"] == expected, f"Got: {d['annual_totals']}"


def test_gttc_totals_match_file():
    d = load_gttc_courses()
    assert d["available"]
    assert d["totals_match"], "Computed totals do not match file's Total row"


def test_gttc_lfl_centres():
    d = load_gttc_courses()
    assert d["available"]
    assert set(d["lfl_centres"]) == {"Mysuru", "Dandeli", "Kalaburgi"}, \
        f"LFL centres: {d['lfl_centres']}"


def test_gttc_lfl_annual():
    d = load_gttc_courses()
    assert d["available"]
    expected = {"2018-19": 1040, "2019-20": 2071, "2020-21": 975, "2021-22": 1641}
    assert d["lfl_annual"] == expected, f"Got: {d['lfl_annual']}"


def test_gttc_coverage():
    d = load_gttc_courses()
    assert d["available"]
    cov = d["coverage"]
    assert cov["cells"] == 40, f"Expected 40 cells, got {cov['cells']}"
    assert cov["filled"] == 23, f"Expected 23 filled cells, got {cov['filled']}"
    assert abs(cov["pct"] - 57.5) < 0.5, f"Coverage pct: {cov['pct']}"


def test_gttc_partner_totals():
    d = load_gttc_courses()
    assert d["available"]
    partners = d["partner_totals"]
    # Siemens should be largest
    siemens = next((v for k, v in partners.items() if "Siemens" in k), None)
    assert siemens is not None, "Siemens partner not found"
    assert siemens == 6655, f"Siemens total: {siemens}"


def test_gttc_mysuru_share():
    d = load_gttc_courses()
    assert d["available"]
    mysuru = next((c for c in d["centres"] if c["centre"] == "Mysuru"), None)
    assert mysuru is not None
    share = mysuru["total"] / d["grand_total"] * 100
    assert abs(share - 34.6) < 0.5, f"Mysuru share: {share}"


def test_gttc_yoy():
    d = load_gttc_courses()
    assert d["available"]
    yoy = d["yoy_pct"]
    assert abs(yoy.get("2019-20", 0) - 141.8) < 1.0, f"YoY 2019-20: {yoy.get('2019-20')}"
    assert abs(yoy.get("2020-21", 0) - (-17.1)) < 1.0, f"YoY 2020-21: {yoy.get('2020-21')}"
    assert abs(yoy.get("2021-22", 0) - 16.0) < 1.0, f"YoY 2021-22: {yoy.get('2021-22')}"


def test_gttc_no_missing_data_for_lfl():
    """LFL centres must have no None values in any year."""
    d = load_gttc_courses()
    yrs = d["years"]
    lfl_names = d["lfl_centres"]
    for c in d["centres"]:
        if c["centre"] in lfl_names:
            for y in yrs:
                assert c.get(y) is not None, f"{c['centre']} missing year {y}"


# ── GTTC Passed ───────────────────────────────────────────────────────────────

def test_gttc_passed_available():
    d = load_gttc_passed()
    assert d["available"], "GTTC passed file not available"


def test_gttc_passed_coe_match():
    """CoE passed counts should match GTTC short-term yearly totals."""
    gttc = load_gttc_courses()
    passed = load_gttc_passed()
    assert gttc["available"] and passed["available"]
    coe = passed["coe_counts"]
    # 2019 → 2019-20, 2020 → 2020-21, 2021 → 2021-22
    assert int(coe["2019"]) == gttc["annual_totals"]["2019-20"], \
        f"CoE 2019={coe['2019']} vs GTTC 2019-20={gttc['annual_totals']['2019-20']}"
    assert int(coe["2020"]) == gttc["annual_totals"]["2020-21"]
    assert int(coe["2021"]) == gttc["annual_totals"]["2021-22"]


# ── Census ────────────────────────────────────────────────────────────────────

def test_census_available():
    d = load_census()
    assert d["available"], "Census file not available"


def test_census_total_persons():
    d = load_census()
    assert d["available"]
    assert d["total_persons"] == 4473682, f"Expected 4,473,682 got {d['total_persons']}"


def test_census_n_districts():
    d = load_census()
    assert d["available"]
    assert d["n_districts"] == 30, f"Expected 30 districts, got {d['n_districts']}"


def test_census_rural_urban_sum():
    d = load_census()
    assert d["available"]
    assert d["rural_total"] + d["urban_total"] == d["total_persons"], \
        "Rural + Urban != Total"


def test_census_agri_share():
    d = load_census()
    assert d["available"]
    assert 60 < d["agri_share_pct"] < 70, f"Agri share: {d['agri_share_pct']}"


def test_census_female_share():
    d = load_census()
    assert d["available"]
    assert 50 < d["female_share_pct"] < 65, f"Female share: {d['female_share_pct']}"


# ── SLSWCC ────────────────────────────────────────────────────────────────────

def test_slswcc_available():
    d = load_slswcc()
    assert d["available"], "SLSWCC file not available"


def test_slswcc_n_units():
    d = load_slswcc()
    assert d["available"]
    assert d["n_units"] == 307, f"Expected 307 units, got {d['n_units']}"


def test_slswcc_employment():
    d = load_slswcc()
    assert d["available"]
    assert d["total_employment"] == 85694, f"Expected 85694, got {d['total_employment']}"


def test_slswcc_sector_harmonisation():
    d = load_slswcc()
    assert d["available"]
    assert d["clean_sector_count"] < d["raw_sector_count"] or d["clean_sector_count"] <= 21, \
        "Sector normalisation did not reduce count"


# ── Quality checks ─────────────────────────────────────────────────────────────

def test_quality_checks_run():
    result = run_all_checks()
    assert "checks" in result
    assert "summary" in result
    assert result["summary"]["total"] > 0


def test_quality_no_unexpected_failures():
    result = run_all_checks()
    # Only expected failures: cross-source period compatibility (WARNING) and crosswalk (NOT_CHECKED)
    hard_fails = [
        c for c in result["checks"]
        if c["status"] == "FAIL" and "availability" not in c["check"].lower()
    ]
    # No unexpected hard failures
    assert len(hard_fails) == 0, f"Unexpected FAIL checks: {hard_fails}"


# ── Missing file graceful degradation ─────────────────────────────────────────

def test_load_result_has_available_key():
    """Every loader must return a dict with 'available' key."""
    from data_loader import load_gttc_courses, load_gttc_passed, load_census
    from data_loader import load_enrolment_2021, load_slswcc, load_enrolment_2019
    for fn in [load_gttc_courses, load_gttc_passed, load_census,
               load_enrolment_2021, load_slswcc, load_enrolment_2019]:
        result = fn()
        assert "available" in result, f"{fn.__name__} missing 'available' key"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
