"""Compatibility entry point for the published GRACE in-hospital point model.

The previous generic weighted-sum demo was NOT a GRACE risk calculator.
"""
import csv

from grace import calculate_grace_score
from cli import main as cli_main

_REQUIRED = ("age", "heart_rate", "systolic_bp", "creatinine", "killip_class")


def _integer(value, name):
    number = float(value)
    if not number.is_integer():
        raise ValueError(f"{name} must be a whole number")
    return int(number)


def _boolean(value, name):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.strip().lower() in ("true", "yes", "1"):
            return True
        if value.strip().lower() in ("false", "no", "0", ""):
            return False
    raise ValueError(f"{name} must be true or false")


def calculate_metrics(**kwargs):
    """Calculate the historical GRACE score from named clinical parameters."""
    missing = [name for name in _REQUIRED if name not in kwargs or kwargs[name] in (None, "")]
    if missing:
        raise ValueError("Missing required GRACE parameters: " + ", ".join(missing))
    result = calculate_grace_score(
        age=_integer(kwargs["age"], "age"),
        heart_rate=_integer(kwargs["heart_rate"], "heart_rate"),
        systolic_bp=_integer(kwargs["systolic_bp"], "systolic_bp"),
        creatinine=float(kwargs["creatinine"]),
        killip_class=_integer(kwargs["killip_class"], "killip_class"),
        cardiac_arrest=_boolean(kwargs.get("cardiac_arrest", False), "cardiac_arrest"),
        st_deviation=_boolean(kwargs.get("st_deviation", False), "st_deviation"),
        elevated_markers=_boolean(kwargs.get("elevated_markers", False), "elevated_markers"),
    )
    # Maintain prior convenience aliases, with the actual GRACE definitions.
    return {
        **result,
        "score": result["grace_score"],
        "classification": result["in_hospital_risk_category"],
        "clinical_recommendation": result["treatment_recommendation"],
    }


def process_batch(input_csv: str, output_csv: str) -> None:
    """Write GRACE scores for a CSV. Fail on invalid data rather than fabricate a score."""
    with open(input_csv, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        original_fields = reader.fieldnames or []
        if not set(_REQUIRED).issubset(original_fields):
            raise ValueError("CSV requires columns: " + ", ".join(_REQUIRED))
        rows = list(reader)
    result_fields = ["grace_score", "in_hospital_risk_category",
                     "in_hospital_mortality_nomogram", "model_limitations"]
    if any(field in original_fields for field in result_fields):
        raise ValueError("Input CSV uses a reserved result column")
    output = []
    for number, row in enumerate(rows, start=2):
        try:
            result = calculate_metrics(**row)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid record on CSV line {number}: {exc}") from exc
        output.append({**row, **{name: result[name] for name in result_fields}})
    with open(output_csv, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=original_fields + result_fields)
        writer.writeheader()
        writer.writerows(output)
    print(f"Processed {len(rows)} records -> {output_csv}")


def main(argv=None):
    """Forward to the supported clinical CLI, preserving this module's entry point."""
    return cli_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
