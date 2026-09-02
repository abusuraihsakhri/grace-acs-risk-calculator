# GRACE Acs Risk Calculator

> **Domain:** Cardiovascular Medicine & Hemodynamic Analytics  
> **Reference Guidelines & Standards:** `AHA/ACC Practice Guidelines & ESC Clinical Standards`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

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

GRACE 2.0 ACS Risk Calculator
Computes GRACE in-hospital and 6-month post-discharge mortality in acute coronary syndromes.

Zero-dependency Python implementation with single and batch evaluation.
Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`describe_killip()`**: Return a clinical description for a Killip class (1-4).
- **`calculate_grace_score()`**: Calculate the GRACE ACS Risk Score and return a full result dict.

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
- **`format_result()`**: Return a human-readable multi-line summary of a GRACE result.
- **`calculate_metrics()`**: Core domain algorithm for grace-acs-risk-calculator.
- **`process_single()`** — calculates and validates process_single parameters.

---

## 📐 Mathematical Formulation & Logic

```text
  """Calculate the GRACE ACS Risk Score and return a full result dict.
  """Return (range_str, risk_category) for in-hospital mortality."""
  return ("<0.2%", "Low")
  return ("0.2-0.4%", "Low")
  return ("0.4-0.9%", "Low-Intermediate")
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --age <value> --hr <value> --sbp <value> --creatinine <value>
```

### Parameter Reference
- `--age`: Specifies input measurement or parameter value.
- `--hr`: Specifies input measurement or parameter value.
- `--sbp`: Specifies input measurement or parameter value.
- `--creatinine`: Specifies input measurement or parameter value.
- `--killip`: Specifies input measurement or parameter value.
- `--st-deviation`: Specifies input measurement or parameter value.
- `--elevated-markers`: Specifies input measurement or parameter value.
- `--class`: Specifies input measurement or parameter value.
- `---`: Specifies input measurement or parameter value.
- `--cardiac-arrest`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Parameter / observation metric | Required |
| `v1` | Parameter / observation metric | Required |
| `v2` | Parameter / observation metric | Required |
| `v3` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t grace-acs-risk-calculator .
docker run -p 8000:8000 grace-acs-risk-calculator
```
