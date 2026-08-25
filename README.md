# GRACE ACS Risk Score Calculator

A zero-dependency Python implementation of the **GRACE (Global Registry of Acute Coronary Events)** risk score for patients presenting with Acute Coronary Syndromes (ACS).

## What This Actually Does

This calculator implements the validated GRACE risk scoring system to estimate **in-hospital** and **6-month mortality** in patients with STEMI, NSTEMI, or unstable angina. It includes both the original GRACE score (2003) with categorical risk bands and the updated GRACE 2.0 model (2014) with continuous probability estimates.

**This is a clinical decision support tool — not a substitute for clinical judgment.**

## The GRACE Score

The GRACE score uses 8 variables collected at presentation:

| Variable | Range | Max Points |
|----------|-------|------------|
| Age | ≥90 → 100 pts | 100 |
| Heart rate | ≥200 bpm → 46 pts | 46 |
| Systolic BP | <80 mmHg → 63 pts | 63 |
| Creatinine | ≥4.0 mg/dL → 31 pts | 31 |
| Killip class | Class IV → 64 pts | 64 |
| Cardiac arrest at admission | Yes → 43 pts | 43 |
| ST-segment deviation | Yes → 30 pts | 30 |
| Elevated cardiac markers | Yes → 15 pts | 15 |

**Maximum possible score: ~372 points**

### Risk Stratification

**In-hospital mortality:**
| GRACE Score | Mortality | Risk |
|-------------|-----------|------|
| ≤60 | <0.2% | Low |
| 61-89 | 0.2-0.4% | Low |
| 90-119 | 0.4-0.9% | Low-Intermediate |
| 120-149 | 0.9-2.3% | Intermediate |
| 150-179 | 2.3-5.1% | Intermediate-High |
| 180-209 | 5.1-10% | High |
| ≥210 | >10% | Very High |

**6-month mortality:**
| GRACE Score | Mortality | Risk |
|-------------|-----------|------|
| ≤88 | <3% | Low |
| 89-118 | 3-8% | Intermediate |
| 119-148 | 8-19% | High |
| ≥149 | >19% | Very High |

### GRACE 2.0

The 2014 update provides continuous mortality estimates using a logistic regression model, giving more precise probability percentages rather than broad ranges.

## Installation

No dependencies required. Python 3.8+ stdlib only.

```bash
git clone <repo-url>
cd grace-acs-risk-calculator
```

## Usage

### Single Patient (CLI)

```bash
python cli.py calculate --age 65 --hr 85 --sbp 130 --creatinine 1.1 --killip 1
```

With risk factors:

```bash
python cli.py calculate --age 72 --hr 110 --sbp 95 --creatinine 1.8 --killip 2 \
                         --st-deviation --elevated-markers
```

JSON output:

```bash
python cli.py calculate --age 65 --hr 85 --sbp 130 --creatinine 1.1 --killip 1 --json
```

### Killip Classification Helper

```bash
python cli.py killip --class 2
# Output: Killip Class 2: Mild heart failure — rales, elevated JVP, or S3 gallop
```

### Batch Processing

Create a CSV with columns: `age`, `heart_rate`, `systolic_bp`, `creatinine`, `killip_class`, and optionally `cardiac_arrest`, `st_deviation`, `elevated_markers`.

```bash
python cli.py batch -i patients.csv -o results.csv
```

### Python API

```python
from grace import calculate_grace_score, format_result

result = calculate_grace_score(
    age=65,
    heart_rate=85,
    systolic_bp=130,
    creatinine=1.1,
    killip_class=1,
    cardiac_arrest=False,
    st_deviation=True,
    elevated_markers=True,
)

print(f"GRACE Score: {result['grace_score']}")
print(f"In-hospital mortality: {result['in_hospital_mortality_pct']}%")
print(f"6-month mortality: {result['six_month_mortality_pct']}%")
print(f"Risk category: {result['in_hospital_risk_category']}")
print(f"Treatment: {result['treatment_recommendation']}")

# Formatted output
print(format_result(result))
```

## Running Tests

```bash
python -m pytest tests/test_grace.py -v
```

## Clinical References

1. Fox KAA, Dabbous OH, Goldberg RJ, et al. "Prediction of risk of death and myocardial infarction in the six months after presentation with acute coronary syndrome: prospective multinational observational study (GRACE)." *BMJ*. 2006;333(7578):1091.
2. Fox KAA, Fitzgerald G, Puymirat E, et al. "Should patients with acute coronary disease be stratified for management according to their risk? Derivation, external validation and outcomes using the updated GRACE risk score." *BMJ Open*. 2014;4(2):e004425.
3. Amsterdam EA, Wenger NK, Brindis RG, et al. "2014 AHA/ACC Guideline for the Management of Patients with Non-ST-Elevation Acute Coronary Syndromes." *J Am Coll Cardiol*. 2014;64(24):e139-e228.

## Limitations

- This tool does not account for all clinical variables (e.g., prior revascularization, diabetes status, weight, or medication use at presentation).
- The GRACE score was derived and validated in specific populations; performance may vary in underrepresented groups.
- Always use clinical judgment alongside any risk score.
- This software is not a medical device and has not been cleared by any regulatory authority.

## License

MIT License. See [LICENSE](LICENSE).
