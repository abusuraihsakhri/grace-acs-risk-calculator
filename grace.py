"""Original GRACE (Granger 2003) in-hospital ACS bedside point calculator.

This module implements ONLY the published eight-variable integer nomogram.
It does not implement GRACE 2.0 continuous probabilities or a six-month model.

Source: Granger CB et al. Arch Intern Med. 2003;163:2345-2353.
DOI: 10.1001/archinte.163.19.2345
Risk thresholds: ESC NSTE-ACS risk stratification (<=108 / 109-140 / >140).
"""

import math
from typing import Any, Dict, List, Tuple

_AGE_TABLE: List[Tuple[int, int]] = [
    (30, 8), (40, 25), (50, 41), (60, 58), (70, 75), (80, 91), (90, 100)
]
_HR_TABLE: List[Tuple[int, int]] = [
    (50, 3), (70, 9), (90, 15), (110, 24), (150, 38), (200, 46)
]
_CREATININE_TABLE: List[Tuple[float, int]] = [
    (0.0, 1), (0.4, 4), (0.8, 7), (1.2, 10),
    (1.6, 13), (2.0, 21), (4.0, 28)
]
_KILLIP_TABLE = {1: 0, 2: 20, 3: 39, 4: 59}
_CARDIAC_ARREST_POINTS = 39
_ST_DEVIATION_POINTS = 28
_ELEVATED_MARKERS_POINTS = 14

# Published 2003 nomogram readout. These are labeled score anchors, NOT
# individually calibrated continuous GRACE 2.0 predictions.
_NOMOGRAM = [
    (60, 0.2), (70, 0.3), (80, 0.4), (90, 0.6), (100, 0.8),
    (110, 1.1), (120, 1.6), (130, 2.1), (140, 2.9),
    (150, 3.9), (160, 5.4), (170, 7.3), (180, 9.8),
    (190, 13.0), (200, 18.0), (210, 23.0),
    (220, 29.0), (230, 36.0), (240, 44.0), (250, 52.0)
]


def _lookup_bracket(value: float, table: List[Tuple[float, int]]) -> int:
    result = 0
    for threshold, points in table:
        if value >= threshold:
            result = points
        else:
            break
    return result


def _lookup_creatinine(creatinine_mg_dl: float) -> int:
    # Comparisons use original units and do not truncate near boundaries.
    return _lookup_bracket(creatinine_mg_dl, _CREATININE_TABLE)


def _lookup_sbp(sbp: int) -> int:
    if sbp < 80:
        return 58
    if sbp < 100:
        return 53
    if sbp < 120:
        return 43
    if sbp < 140:
        return 34
    if sbp < 160:
        return 24
    if sbp < 200:
        return 10
    return 0


def describe_killip(class_number: int) -> str:
    descriptions = {
        1: "No clinical signs of heart failure",
        2: "Mild heart failure — rales, elevated JVP, or S3 gallop",
        3: "Severe heart failure — acute pulmonary edema",
        4: "Cardiogenic shock — hypotension, tachycardia, altered mental status",
    }
    if type(class_number) is not int or class_number not in descriptions:
        raise ValueError("Killip class must be an integer from 1 to 4")
    return descriptions[class_number]


def _in_hospital_mortality(score: int) -> Tuple[str, str]:
    """Return the *historical nominal* in-hospital band and ESC score tier."""
    if score <= 108:
        return ("<1% (historical ESC band)", "Low")
    if score <= 140:
        return ("1–3% (historical ESC band)", "Intermediate")
    return (">3% (historical ESC band)", "High")


def _six_month_mortality(score: int):
    """A six-month prediction requires another model with different inputs."""
    raise NotImplementedError(
        "The six-month GRACE model cannot be calculated from the "
        "eight-variable in-hospital score."
    )


def _grace2_mortality(*args, **kwargs):
    """GRACE 2.0 is nonlinear; generic score-to-logit conversion is invalid."""
    raise NotImplementedError(
        "GRACE 2.0 continuous probabilities require the published "
        "endpoint-specific model, not a logistic conversion of the point total."
    )


def _nomogram_lookup(score: int) -> Tuple[float, str]:
    if score <= 60:
        return (0.2, "≤0.2% (score ≤60; published nomogram)")
    if score >= 250:
        return (52.0, "≥52% (score ≥250; published nomogram)")
    anchor, estimate = _NOMOGRAM[0]
    for candidate, value in _NOMOGRAM:
        if candidate > score:
            break
        anchor, estimate = candidate, value
    return (estimate, f"{estimate:g}% (published score-{anchor} anchor; not interpolated)")


def _treatment_recommendation(score: int, killip_class: int) -> str:
    if killip_class == 4:
        return (
            "Cardiogenic shock requires immediate clinical assessment regardless "
            "of this point score. Follow the applicable ACS emergency pathway."
        )
    if score > 140:
        return (
            "GRACE >140 is one high-risk criterion in NSTE-ACS guidelines; "
            "consider early invasive evaluation in the full clinical context. "
            "This calculator does not prescribe treatment."
        )
    return (
        "Interpret the score with ECG, troponin, symptoms and haemodynamic status. "
        "A low/intermediate score does not exclude ACS or remove an indication "
        "for urgent management."
    )


def _validate_int(label: str, value: Any, low: int, high: int) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an integer in {low}–{high}")


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
    """Return a historical 2003 GRACE in-hospital score and component points.

    No individual six-month or GRACE 2.0 risk is calculated. Mortality values
    are published in-hospital nomogram *anchors*, not interpolated predictions.
    """
    _validate_int("Age", age, 18, 120)
    _validate_int("Heart rate", heart_rate, 20, 300)
    _validate_int("Systolic BP", systolic_bp, 50, 300)
    if isinstance(creatinine, bool) or not isinstance(creatinine, (int, float)) or not math.isfinite(creatinine) or not 0.1 <= creatinine <= 20.0:
        raise ValueError("Creatinine must be a finite number in 0.1–20.0 mg/dL")
    _validate_int("Killip class", killip_class, 1, 4)
    for label, value in [
        ("Cardiac arrest", cardiac_arrest),
        ("ST deviation", st_deviation),
        ("Elevated markers", elevated_markers),
    ]:
        if type(value) is not bool:
            raise ValueError(f"{label} must be boolean")

    parts = {
        "age_points": _lookup_bracket(age, _AGE_TABLE),
        "hr_points": _lookup_bracket(heart_rate, _HR_TABLE),
        "sbp_points": _lookup_sbp(systolic_bp),
        "creatinine_points": _lookup_creatinine(creatinine),
        "killip_points": _KILLIP_TABLE[killip_class],
        "cardiac_arrest_points": _CARDIAC_ARREST_POINTS if cardiac_arrest else 0,
        "st_deviation_points": _ST_DEVIATION_POINTS if st_deviation else 0,
        "elevated_markers_points": _ELEVATED_MARKERS_POINTS if elevated_markers else 0,
    }
    score = sum(parts.values())
    nominal_pct, nomogram_label = _nomogram_lookup(score)
    risk_band, category = _in_hospital_mortality(score)
    return {
        "grace_score": score,
        **parts,
        "model": "GRACE original 2003 in-hospital nomogram",
        "in_hospital_mortality_pct": nominal_pct,
        "in_hospital_mortality_range": risk_band,
        "in_hospital_mortality_nomogram": nomogram_label,
        "in_hospital_risk_category": category,
        "six_month_mortality_pct": None,
        "six_month_mortality_range": None,
        "six_month_risk_category": None,
        "grace2_in_hospital_mortality_pct": None,
        "grace2_six_month_mortality_pct": None,
        "killip_description": describe_killip(killip_class),
        "treatment_recommendation": _treatment_recommendation(score, killip_class),
        "model_limitations": (
            "Historical in-hospital point model only. Nomogram values are "
            "reported anchors, not continuous GRACE 2.0 predictions; "
            "six-month prognosis is not calculated."
        ),
    }


def format_result(result: Dict[str, Any]) -> str:
    lines = [
        "GRACE SCORE — 2003 IN-HOSPITAL MODEL",
        f"Score: {result['grace_score']} / 372",
        f"Risk tier: {result['in_hospital_risk_category']}",
        f"Historical risk band: {result['in_hospital_mortality_range']}",
        f"Historical nomogram: {result['in_hospital_mortality_nomogram']}",
        "Component points:",
    ]
    for name in (
        "age_points", "hr_points", "sbp_points", "creatinine_points",
        "killip_points", "cardiac_arrest_points",
        "st_deviation_points", "elevated_markers_points",
    ):
        lines.append(f"  {name}: {result[name]}")
    lines += [
        "Six-month mortality: not calculated",
        "GRACE 2.0 probability: not calculated",
        "TREATMENT CONTEXT: " + result["treatment_recommendation"],
        "LIMITATIONS: " + result["model_limitations"],
        "Not a substitute for clinical assessment or validated GRACE 2.0 software.",
    ]
    return "\n".join(lines)
