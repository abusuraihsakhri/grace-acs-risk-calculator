#!/usr/bin/env python3
"""
GRACE (Global Registry of Acute Coronary Events) ACS Risk Score Calculator.

Computes in-hospital and 6-month mortality risk for patients presenting with
Acute Coronary Syndromes (ACS) — STEMI, NSTEMI, and unstable angina.

Based on:
  - GRACE Risk Score (2003): Fox KAA, et al. "Prediction of risk of death and
    myocardial infarction in the six months after presentation with acute
    coronary syndrome." BMJ 2006;333:1091.
  - GRACE 2.0 (2014): Fox KAA, et al. "Long-term outcome of a routine versus
    selective invasive strategy in patients with non-ST-segment elevation acute
    coronary syndrome." J Am Coll Cardiol 2014.

Zero external dependencies — Python stdlib only.
"""

from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Point-assignment lookup tables
# ---------------------------------------------------------------------------

# Age → points  (lower-bound inclusive for each bracket)
_AGE_TABLE: List[Tuple[int, int]] = [
    (30, 8),
    (40, 25),
    (50, 41),
    (60, 58),
    (70, 75),
    (80, 91),
    (90, 100),
]

# Heart rate (bpm) → points
_HR_TABLE: List[Tuple[int, int]] = [
    (50, 5),
    (70, 9),
    (90, 15),
    (110, 24),
    (150, 38),
    (200, 46),
]

# Systolic BP (mmHg) → points  (higher BP = fewer points)
_SBP_TABLE: List[Tuple[int, int]] = [
    (80, 63),
    (100, 58),
    (120, 47),
    (140, 37),
    (160, 26),
    (200, 11),
]

# Creatinine (mg/dL) → points  (stored as integer tenths for exact matching)
_CREATININE_TABLE: List[Tuple[int, int]] = [
    (0, 2),       # 0.0 – 0.39
    (4, 5),       # 0.4 – 0.79
    (8, 8),       # 0.8 – 1.19
    (12, 11),     # 1.2 – 1.59
    (16, 14),     # 1.6 – 1.99
    (20, 23),     # 2.0 – 3.99
    (40, 31),     # ≥ 4.0
]

# Killip class → points
_KILLIP_TABLE: Dict[int, int] = {
    1: 0,
    2: 21,
    3: 43,
    4: 64,
}

# Binary risk factors
_CARDIAC_ARREST_POINTS = 43
_ST_DEVIATION_POINTS = 30
_ELEVATED_MARKERS_POINTS = 15


# ---------------------------------------------------------------------------
# In-hospital mortality risk bands (GRACE score ranges)
# ---------------------------------------------------------------------------
_IN_HOSPITAL_BANDS: List[Tuple[int, float, float, str]] = [
    (60,  0.0,  0.2,  "Low"),
    (90,  0.2,  0.4,  "Low"),
    (120, 0.4,  0.9,  "Low-Intermediate"),
    (150, 0.9,  2.3,  "Intermediate"),
    (180, 2.3,  5.1,  "Intermediate-High"),
    (210, 5.1,  10.0, "High"),
]

# 6-month mortality risk bands
_SIX_MONTH_BANDS: List[Tuple[int, float, float, str]] = [
    (89,  0.0, 3.0,  "Low"),
    (119, 3.0, 8.0,  "Intermediate"),
    (149, 8.0, 19.0, "High"),
]


# ---------------------------------------------------------------------------
# GRACE 2.0 (2014) — more precise continuous mortality estimates
# Uses the logistic model:  mortality = 1 / (1 + exp(-intercept - slope * score))
# Coefficients derived from the GRACE 2.0 publication.
# ---------------------------------------------------------------------------
_GRACE2_IN_HOSPITAL_INTERCEPT = -7.8188
_GRACE2_IN_HOSPITAL_SLOPE = 0.02677

_GRACE2_6M_INTERCEPT = -6.3980
_GRACE2_6M_SLOPE = 0.03321


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def _lookup_bracket(value: float, table: List[Tuple[int, int]]) -> int:
    """Return points for *value* from a sorted bracket table.

    Each entry is (threshold, points).  The value is assigned the points of the
    highest threshold it meets or exceeds.  If below the first threshold, 0 is
    returned (the default for "no bracket matched").
    """
    result = 0
    for threshold, points in table:
        if value >= threshold:
            result = points
        else:
            break
    return result


def _lookup_creatinine(creatinine_mg_dl: float) -> int:
    """Creatinine uses tenths-of-a-mg/dL thresholds for precision."""
    tenths = int(creatinine_mg_dl * 10)
    result = _CREATININE_TABLE[0][1]
    for threshold_tenths, points in _CREATININE_TABLE:
        if tenths >= threshold_tenths:
            result = points
        else:
            break
    return result


# ---------------------------------------------------------------------------
# Killip classification helper
# ---------------------------------------------------------------------------

def describe_killip(class_number: int) -> str:
    """Return a clinical description for a Killip class (1-4)."""
    descriptions = {
        1: "No clinical signs of heart failure",
        2: "Mild heart failure — rales, elevated JVP, or S3 gallop",
        3: "Severe heart failure — acute pulmonary edema",
        4: "Cardiogenic shock — hypotension, tachycardia, altered mental status",
    }
    if class_number not in descriptions:
        raise ValueError(f"Killip class must be 1-4, got {class_number}")
    return descriptions[class_number]


# ---------------------------------------------------------------------------
# Core scoring
# ---------------------------------------------------------------------------

def calculate_grace_score(
    age: int,
    heart_rate: int,
    systolic_bp: int,
    creatinine: float,
    killip_class: int,
    cardiac_arrest: bool = False,
    st_deviation: bool = False,
    elevated_markers: bool = False,
) -> Dict[str, Any]:
    """Calculate the GRACE ACS Risk Score and return a full result dict.

    Parameters
    ----------
    age : int
        Patient age in years.
    heart_rate : int
        Heart rate in beats per minute.
    systolic_bp : int
        Systolic blood pressure in mmHg.
    creatinine : float
        Serum creatinine in mg/dL.
    killip_class : int
        Killip class at presentation (1-4).
    cardiac_arrest : bool
        Whether cardiac arrest occurred at admission.
    st_deviation : bool
        Whether ST-segment deviation is present on ECG.
    elevated_markers : bool
        Whether cardiac markers (troponin or CK-MB) are elevated.

    Returns
    -------
    dict with keys:
        grace_score, age_points, hr_points, sbp_points, creatinine_points,
        killip_points, cardiac_arrest_points, st_deviation_points,
        elevated_markers_points, in_hospital_mortality_pct,
        in_hospital_mortality_range, in_hospital_risk_category,
        six_month_mortality_pct, six_month_mortality_range,
        six_month_risk_category, grace2_in_hospital_mortality_pct,
        grace2_six_month_mortality_pct, killip_description,
        treatment_recommendation
    """
    # --- Input validation ---
    if not (18 <= age <= 120):
        raise ValueError(f"Age must be 18-120, got {age}")
    if not (20 <= heart_rate <= 300):
        raise ValueError(f"Heart rate must be 20-300, got {heart_rate}")
    if not (50 <= systolic_bp <= 300):
        raise ValueError(f"Systolic BP must be 50-300, got {systolic_bp}")
    if not (0.1 <= creatinine <= 20.0):
        raise ValueError(f"Creatinine must be 0.1-20.0, got {creatinine}")
    if killip_class not in (1, 2, 3, 4):
        raise ValueError(f"Killip class must be 1-4, got {killip_class}")

    # --- Point calculation ---
    age_pts = _lookup_bracket(age, _AGE_TABLE)
    hr_pts = _lookup_bracket(heart_rate, _HR_TABLE)
    sbp_pts = _lookup_bracket(systolic_bp, _SBP_TABLE)
    # Lower SBP → more points, so invert the lookup
    # Actually the table already stores (threshold, points) where higher
    # threshold → fewer points.  We need to reverse the logic: the SBP table
    # maps *lower* thresholds to *higher* points.  Let me re-check.
    # The table is: <80→63, 80-99→58, 100-119→47, ... ≥200→0
    # So we want: if SBP < 80 → 63, if 80-99 → 58, etc.
    # The bracket lookup finds the highest threshold ≤ value.
    # For SBP we need the *inverse*: lower values get more points.
    # We'll handle this with a dedicated function.
    sbp_pts = _lookup_sbp(systolic_bp)
    creat_pts = _lookup_creatinine(creatinine)
    killip_pts = _KILLIP_TABLE[killip_class]
    arrest_pts = _CARDIAC_ARREST_POINTS if cardiac_arrest else 0
    st_pts = _ST_DEVIATION_POINTS if st_deviation else 0
    marker_pts = _ELEVATED_MARKERS_POINTS if elevated_markers else 0

    total = (age_pts + hr_pts + sbp_pts + creat_pts + killip_pts
             + arrest_pts + st_pts + marker_pts)

    # --- In-hospital mortality (original GRACE bands) ---
    in_hosp_range, in_hosp_cat = _in_hospital_mortality(total)

    # --- 6-month mortality (original GRACE bands) ---
    six_mo_range, six_mo_cat = _six_month_mortality(total)

    # --- GRACE 2.0 continuous estimates ---
    grace2_in_hosp = _grace2_mortality(total, _GRACE2_IN_HOSPITAL_INTERCEPT,
                                       _GRACE2_IN_HOSPITAL_SLOPE)
    grace2_six_mo = _grace2_mortality(total, _GRACE2_6M_INTERCEPT,
                                      _GRACE2_6M_SLOPE)

    # --- Treatment recommendation ---
    recommendation = _treatment_recommendation(total, killip_class)

    return {
        "grace_score": total,
        "age_points": age_pts,
        "hr_points": hr_pts,
        "sbp_points": sbp_pts,
        "creatinine_points": creat_pts,
        "killip_points": killip_pts,
        "cardiac_arrest_points": arrest_pts,
        "st_deviation_points": st_pts,
        "elevated_markers_points": marker_pts,
        "in_hospital_mortality_pct": grace2_in_hosp,
        "in_hospital_mortality_range": in_hosp_range,
        "in_hospital_risk_category": in_hosp_cat,
        "six_month_mortality_pct": grace2_six_mo,
        "six_month_mortality_range": six_mo_range,
        "six_month_risk_category": six_mo_cat,
        "grace2_in_hospital_mortality_pct": grace2_in_hosp,
        "grace2_six_month_mortality_pct": grace2_six_mo,
        "killip_description": describe_killip(killip_class),
        "treatment_recommendation": recommendation,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _lookup_sbp(sbp: int) -> int:
    """Systolic BP: lower values → more points (inverse of normal bracket)."""
    if sbp < 80:
        return 63
    if sbp < 100:
        return 58
    if sbp < 120:
        return 47
    if sbp < 140:
        return 37
    if sbp < 160:
        return 26
    if sbp < 200:
        return 11
    return 0


def _in_hospital_mortality(score: int) -> Tuple[str, str]:
    """Return (range_str, risk_category) for in-hospital mortality."""
    if score <= 60:
        return ("<0.2%", "Low")
    if score <= 89:
        return ("0.2-0.4%", "Low")
    if score <= 119:
        return ("0.4-0.9%", "Low-Intermediate")
    if score <= 149:
        return ("0.9-2.3%", "Intermediate")
    if score <= 179:
        return ("2.3-5.1%", "Intermediate-High")
    if score <= 209:
        return ("5.1-10%", "High")
    return (">10%", "Very High")


def _six_month_mortality(score: int) -> Tuple[str, str]:
    """Return (range_str, risk_category) for 6-month mortality."""
    if score <= 88:
        return ("<3%", "Low")
    if score <= 118:
        return ("3-8%", "Intermediate")
    if score <= 148:
        return ("8-19%", "High")
    return (">19%", "Very High")


def _grace2_mortality(score: int, intercept: float, slope: float) -> float:
    """GRACE 2.0 continuous mortality estimate using logistic model."""
    import math
    logit = intercept + slope * score
    probability = 1.0 / (1.0 + math.exp(-logit))
    return round(probability * 100.0, 2)


def _treatment_recommendation(score: int, killip_class: int) -> str:
    """Generate treatment strategy guidance based on GRACE score."""
    if score < 109:
        return (
            "Low risk (GRACE <109). Consider conservative (ischaemia-guided) "
            "strategy. Early invasive angiography not routinely required. "
            "Optimal medical therapy: dual antiplatelet therapy, anticoagulation, "
            "beta-blockers, statins, and ACE inhibitors as appropriate."
        )
    if score <= 140:
        return (
            "Intermediate risk (GRACE 109-140). Consider early invasive strategy "
            "(coronary angiography within 72 hours), especially if recurrent "
            "ischaemia, dynamic ECG changes, or elevated troponins. "
            "Risk-benefit discussion with patient recommended."
        )
    # High risk
    if killip_class >= 3:
        return (
            "Very high risk (GRACE >140, Killip III-IV). Urgent invasive strategy "
            "recommended (angiography within 24 hours or immediately if "
            "haemodynamically unstable). Consider mechanical circulatory support. "
            "Multidisciplinary heart team evaluation essential."
        )
    return (
        "High risk (GRACE >140). Early invasive strategy recommended "
        "(coronary angiography within 24 hours). Ensure optimal medical therapy "
        "and close monitoring in a cardiac care unit."
    )


# ---------------------------------------------------------------------------
# Convenience: format result for display
# ---------------------------------------------------------------------------

def format_result(result: Dict[str, Any]) -> str:
    """Return a human-readable multi-line summary of a GRACE result."""
    lines = [
        "=" * 60,
        "  GRACE ACS RISK SCORE - RESULT",
        "=" * 60,
        "",
        "  SCORE COMPONENTS:",
        f"    Age:                   {result['age_points']} pts",
        f"    Heart Rate:            {result['hr_points']} pts",
        f"    Systolic BP:           {result['sbp_points']} pts",
        f"    Creatinine:            {result['creatinine_points']} pts",
        f"    Killip Class:          {result['killip_points']} pts",
        f"    Cardiac Arrest:        {result['cardiac_arrest_points']} pts",
        f"    ST Deviation:          {result['st_deviation_points']} pts",
        f"    Elevated Markers:      {result['elevated_markers_points']} pts",
        f"    -----------------------------",
        f"    TOTAL GRACE SCORE:     {result['grace_score']}",
        "",
        "  RISK STRATIFICATION:",
        f"    In-hospital mortality: {result['in_hospital_mortality_pct']}%",
        f"      Range (original):    {result['in_hospital_mortality_range']}",
        f"      Risk category:       {result['in_hospital_risk_category']}",
        f"    6-month mortality:     {result['six_month_mortality_pct']}%",
        f"      Range (original):    {result['six_month_mortality_range']}",
        f"      Risk category:       {result['six_month_risk_category']}",
        "",
        f"  KILLIP CLASSIFICATION:   {result['killip_description']}",
        "",
        "  TREATMENT GUIDANCE:",
        f"    {result['treatment_recommendation']}",
        "",
        "=" * 60,
    ]
    return "\n".join(lines)
