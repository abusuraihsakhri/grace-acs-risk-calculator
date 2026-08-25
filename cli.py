#!/usr/bin/env python3
"""
Command-line interface for the GRACE ACS Risk Score Calculator.

Usage:
    python cli.py calculate --age 65 --hr 85 --sbp 130 --creatinine 1.1 --killip 1
    python cli.py calculate --age 65 --hr 85 --sbp 130 --creatinine 1.1 --killip 2 \
                             --st-deviation --elevated-markers
    python cli.py killip --class 2
    python cli.py batch -i patients.csv -o results.csv

Zero external dependencies — Python stdlib only.
"""

import argparse
import csv
import json
import sys

from grace import calculate_grace_score, describe_killip, format_result


def cmd_calculate(args):
    """Run a single GRACE score calculation."""
    result = calculate_grace_score(
        age=args.age,
        heart_rate=args.hr,
        systolic_bp=args.sbp,
        creatinine=args.creatinine,
        killip_class=args.killip,
        cardiac_arrest=args.cardiac_arrest,
        st_deviation=args.st_deviation,
        elevated_markers=args.elevated_markers,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_result(result))
    return 0


def cmd_killip(args):
    """Describe a Killip class."""
    try:
        desc = describe_killip(args.klass)
        print(f"Killip Class {args.klass}: {desc}")
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_batch(args):
    """Process a CSV file of patients and output GRACE scores."""
    with open(args.input, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    out_fields = fieldnames + [
        "grace_score",
        "in_hospital_mortality_pct",
        "in_hospital_risk_category",
        "six_month_mortality_pct",
        "six_month_risk_category",
        "treatment_recommendation",
    ]
    out_rows = []

    for i, r in enumerate(rows, start=1):
        try:
            result = calculate_grace_score(
                age=int(r["age"]),
                heart_rate=int(r["heart_rate"]),
                systolic_bp=int(r["systolic_bp"]),
                creatinine=float(r["creatinine"]),
                killip_class=int(r["killip_class"]),
                cardiac_arrest=_parse_bool(r.get("cardiac_arrest", "false")),
                st_deviation=_parse_bool(r.get("st_deviation", "false")),
                elevated_markers=_parse_bool(r.get("elevated_markers", "false")),
            )
            row_dict = dict(r)
            row_dict["grace_score"] = result["grace_score"]
            row_dict["in_hospital_mortality_pct"] = result["in_hospital_mortality_pct"]
            row_dict["in_hospital_risk_category"] = result["in_hospital_risk_category"]
            row_dict["six_month_mortality_pct"] = result["six_month_mortality_pct"]
            row_dict["six_month_risk_category"] = result["six_month_risk_category"]
            row_dict["treatment_recommendation"] = result["treatment_recommendation"]
            out_rows.append(row_dict)
        except (ValueError, KeyError) as e:
            print(f"Warning: Row {i} skipped — {e}", file=sys.stderr)

    with open(args.output, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Processed {len(out_rows)}/{len(rows)} records -> {args.output}")
    return 0


def _parse_bool(val: str) -> bool:
    """Parse a string as boolean (handles true/false/yes/no/1/0)."""
    return str(val).strip().lower() in ("true", "yes", "1")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="grace-acs-risk-calculator",
        description="GRACE ACS Risk Score Calculator — in-hospital and 6-month mortality",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- calculate ---
    p_calc = subparsers.add_parser(
        "calculate",
        help="Calculate GRACE score for a single patient",
    )
    p_calc.add_argument("--age", type=int, required=True, help="Age in years")
    p_calc.add_argument("--hr", type=int, required=True, help="Heart rate (bpm)")
    p_calc.add_argument("--sbp", type=int, required=True, help="Systolic BP (mmHg)")
    p_calc.add_argument("--creatinine", type=float, required=True, help="Serum creatinine (mg/dL)")
    p_calc.add_argument("--killip", type=int, required=True, choices=[1, 2, 3, 4],
                        help="Killip class (1-4)")
    p_calc.add_argument("--cardiac-arrest", action="store_true",
                        help="Cardiac arrest at admission")
    p_calc.add_argument("--st-deviation", action="store_true",
                        help="ST-segment deviation on ECG")
    p_calc.add_argument("--elevated-markers", action="store_true",
                        help="Elevated cardiac markers (troponin/CK-MB)")
    p_calc.add_argument("--json", action="store_true",
                        help="Output as JSON instead of formatted text")
    p_calc.set_defaults(func=cmd_calculate)

    # --- killip ---
    p_killip = subparsers.add_parser(
        "killip",
        help="Describe a Killip classification",
    )
    p_killip.add_argument("--class", dest="klass", type=int, required=True,
                          choices=[1, 2, 3, 4], help="Killip class (1-4)")
    p_killip.set_defaults(func=cmd_killip)

    # --- batch ---
    p_batch = subparsers.add_parser(
        "batch",
        help="Batch-process a CSV of patients",
    )
    p_batch.add_argument("-i", "--input", required=True, help="Input CSV file")
    p_batch.add_argument("-o", "--output", default="results.csv", help="Output CSV file")
    p_batch.set_defaults(func=cmd_batch)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
