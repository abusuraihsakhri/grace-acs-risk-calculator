# GRACE ACS Risk Calculator

> **Domain:** Cardiovascular Medicine & Hemodynamic Analytics
> **Reference Guidelines & Standards:** AHA/ACC Practice Guidelines & ESC Clinical Standards

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## What It Does

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

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## Key Capabilities & Algorithmic Modules

### Analytical Functions

- **`describe_killip()`**: Return a clinical description for a Killip class (1-4).
- **`calculate_grace_score()`**: Calculate the GRACE ACS Risk Score and return a full result dict.
- **`format_result()`**: Return a human-readable multi-line summary of a GRACE result.
- **`calculate_metrics()`**: Core domain algorithm for single/batch evaluation.
- **`process_single()`** — calculates and validates parameters.
- **`process_batch()`** — processes CSV files of patients.

### CLI Commands

- **`calculate`** — Calculate GRACE score for a single patient
- **`killip`** — Describe a Killip classification
- **`batch`** — Batch-process a CSV of patients
- **`audit`** — Run an audit task through the supervisor
- **`chat`** — Query the supervisory chat assistant
- **`verify-audit`** — Verify the integrity of the HMAC audit trail

---

## CLI Quickstart & Usage

### 1. Calculate GRACE Score
```bash
python cli.py calculate --age 65 --hr 85 --sbp 130 --creatinine 1.1 --killip 1
python cli.py calculate --age 70 --hr 100 --sbp 90 --creatinine 2.0 --killip 3 --st-deviation --elevated-markers
python cli.py calculate --age 65 --hr 85 --sbp 130 --creatinine 1.1 --killip 1 --json
```

### 2. Killip Classification Helper
```bash
python cli.py killip --class 2
```

### 3. Batch Processing
```bash
python cli.py batch -i patients.csv -o results.csv
```

### 4. Audit & Verification
```bash
python cli.py audit --task-id CLI-001
python cli.py chat "Explain specifications"
python cli.py verify-audit
```

### Parameter Reference
- `--age`: Patient age in years (18-120)
- `--hr`: Heart rate in beats per minute (20-300)
- `--sbp`: Systolic blood pressure in mmHg (50-300)
- `--creatinine`: Serum creatinine in mg/dL (0.1-20.0)
- `--killip`: Killip class at presentation (1-4)
- `--cardiac-arrest`: Cardiac arrest at admission (flag)
- `--st-deviation`: ST-segment deviation on ECG (flag)
- `--elevated-markers`: Elevated cardiac markers (flag)
- `--json`: Output as JSON instead of formatted text

### Input Data Schema (for batch CSV)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `age` | Patient age in years | Required |
| `heart_rate` | Heart rate (bpm) | Required |
| `systolic_bp` | Systolic BP (mmHg) | Required |
| `creatinine` | Serum creatinine (mg/dL) | Required |
| `killip_class` | Killip class (1-4) | Required |
| `cardiac_arrest` | Cardiac arrest at admission | Optional (default: false) |
| `st_deviation` | ST-segment deviation | Optional (default: false) |
| `elevated_markers` | Elevated cardiac markers | Optional (default: false) |

---

## Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances, Claude, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.

---

## Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/grace-acs-risk-calculator.git
cd grace-acs-risk-calculator

# Core module (zero dependencies)
python cli.py calculate --age 65 --hr 85 --sbp 130 --creatinine 1.1 --killip 1

# With web/API support (optional)
pip install -e ".[web]"

# With development dependencies
pip install -e ".[dev]"
```

---

## Container Deployment

```bash
docker build -t grace-acs-risk-calculator .
docker run -p 8000:8000 grace-acs-risk-calculator
```

Or with docker-compose:

```bash
docker-compose up -d
```

---

## Project Structure

```
grace-acs-risk-calculator/
├── grace.py              # Core GRACE scoring algorithm
├── grace_acs.py          # Alternative scoring module with batch support
├── cli.py                # Command-line interface
├── enrichment.py         # Enrichment feature engines
├── simulator.py          # High-throughput stress testing simulator
├── agents/               # Enterprise agent modules
│   ├── base.py           # Security, PHI guard, HMAC audit
│   ├── models.py         # Pydantic data models
│   ├── supervisor.py     # Multi-agent orchestrator
│   ├── workers.py        # Specialized domain workers
│   ├── api.py            # FastAPI REST endpoints
│   ├── metrics.py        # Prometheus metrics collector
│   ├── learning.py       # Bayesian calibration engine
│   └── llm_factory.py    # LLM client factory
├── tests/                # Test suite
│   ├── test_grace.py     # Core algorithm tests
│   ├── test_enrichment.py
│   └── test_grace_acs_risk_calculator.py
├── test_grace_acs.py     # Root-level integration tests
├── pyproject.toml        # Project configuration
├── Dockerfile            # Container build
├── docker-compose.yml    # Container orchestration
└── openapi_spec.json     # OpenAPI 3.1 specification
```
