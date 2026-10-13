# GRACE ACS Risk Calculator

Historical **GRACE 2003 in-hospital ACS point score** implemented in Python and
plain JavaScript. Calculates the eight-factor score (1–372), component points,
and the historical in-hospital risk tier and printed nomogram anchors.

> **Model scope:** This project implements the original Granger et al. (2003)
> bedside *in-hospital* nomogram. It **does not** implement the official
> nonlinear GRACE 2.0 mortality equations, six-month post-discharge mortality,
> or an individualized treatment algorithm. The printed percentage is a
> historical nomogram anchor, **not an interpolated individual prediction**.
> This is an educational reference and is not a medical device.

## Application

The static browser calculator is in [docs/index.html](docs/index.html).
GitHub Pages deployment is configured in
[.github/workflows/pages.yml](.github/workflows/pages.yml); the public Pages
URL should be used only once the deployment has succeeded and the site is
verified. Open the static file directly or start a local server:

~~~sh
python -m http.server 8080 --directory docs
~~~

Open http://localhost:8080 in a modern browser. The web form accepts age,
heart rate, systolic blood pressure, creatinine (mg/dL), Killip class,
cardiac arrest at admission, ST-segment deviation and elevated initial
cardiac biomarkers. It shows the breakdown and can export a JSON result.

Browser calculations run entirely client-side; the static page does not send,
store or track entered data. Do not enter patient identifiers. The optional
FastAPI endpoint processes requests on the configured server, where deployment
operators are responsible for privacy and logging controls. The historical
audit demo in the repository is **not** a verified PHI-deidentification system.

## Python CLI

Requires Python 3.10 or later; core scoring uses the standard library.

~~~sh
python cli.py calculate --age 65 --hr 80 --sbp 130 --creatinine 1.0 --killip 1 --json
python cli.py calculate --age 67 --hr 96 --sbp 128 --creatinine 1.1 --killip 1 --st-deviation --elevated-markers
python cli.py killip --class 3
python cli.py batch -i sample.csv -o results.csv
~~~

The first example scores **108**; the second scores **156**. Required batch
CSV columns are **age,heart_rate,systolic_bp,creatinine,killip_class**, with
optional Boolean columns **cardiac_arrest,st_deviation,elevated_markers**.
Invalid Boolean values are rejected. The grace_acs.calculate_metrics and
grace_acs.process_batch compatibility interfaces use these same clinical
parameters; the previous generic v1/v2/v3 calculation has been withdrawn
because it was not GRACE.

## API and local development

~~~sh
python -m pip install -e ".[dev]"
python -m pytest -q
node --test tests/test_browser.cjs
python cli.py serve --host 127.0.0.1 --port 8000
~~~

Then visit http://localhost:8000/ for the UI and
http://localhost:8000/docs for the API documentation. The clinical endpoint is
**POST /api/grace** with JSON input, e.g.:

~~~json
{
  "age": 65,
  "heart_rate": 80,
  "systolic_bp": 130,
  "creatinine": 1.0,
  "killip_class": 1,
  "cardiac_arrest": false,
  "st_deviation": false,
  "elevated_markers": false
}
~~~

Docker: **docker compose up --build** exposes the app at localhost port 8000.
The optional in-memory audit demo generates an ephemeral HMAC key when
AUDIT_SECRET_KEY is unset; production users needing audit continuity must
inject a strong secret using their infrastructure. Audit records are not a
persisted compliance log. Separate generic supervisor/worker demonstration
modules remain available, but are not validated clinical scoring functions.

## References and limitations

- Granger CB et al. *Predictors of hospital mortality in the global registry
  of acute coronary events*. Arch Intern Med. 2003;163:2345–2353.
  [doi:10.1001/archinte.163.19.2345](https://doi.org/10.1001/archinte.163.19.2345).
- [Official GRACE 2.0 calculator and FAQ](https://www.gracescore.org/):
  a distinct nonlinear multivariable model.
- [ESC 2023 ACS guidelines](https://doi.org/10.1093/eurheartj/ehad191):
  clinical risk stratification and invasive-management context.

The score uses values **at presentation**. The historical
≤108 / 109–140 / >140 tiers should not be treated as independent management
instructions. Interpret the score with the full clinical presentation and
current guidelines. The Python and JavaScript implementations have regression
tests for worked examples, boundary points and published nomogram anchors.
Validation for patient-care deployment has **not** been performed.

**Technology:** Python standard library, optional FastAPI/Pydantic/Uvicorn,
vanilla HTML/CSS/JavaScript. No Pyodide or server-side Python is required for
the static calculator. CI covers Python 3.10–3.13 and Node.js 22; modern
evergreen browsers are targeted.

**License:** [MIT](LICENSE).
