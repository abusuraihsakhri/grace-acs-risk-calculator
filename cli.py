#!/usr/bin/env python3
"""
Command-line interface for the GRACE ACS Risk Score Calculator.

Usage:
    python cli.py calculate --age 65 --hr 85 --sbp 130 --creatinine 1.1 --killip 1
    python cli.py calculate --age 65 --hr 85 --sbp 130 --creatinine 1.1 --killip 2 \
                             --st-deviation --elevated-markers
    python cli.py killip --class 2
    python cli.py batch -i patients.csv -o results.csv
    python cli.py audit --task-id CLI-001
    python cli.py chat "Explain specifications"
    python cli.py verify-audit

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


def cmd_serve(args):
    """Run the optional FastAPI application (requires the web extra)."""
    try:
        import uvicorn
    except ImportError:
        print("Install pip install -e '.[web]' to use the server", file=sys.stderr)
        return 1
    uvicorn.run("agents.api:app", host=args.host, port=args.port)
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
        "in_hospital_mortality_nomogram",
        "in_hospital_risk_category",
        "model_limitations",
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
            row_dict["in_hospital_mortality_nomogram"] = result["in_hospital_mortality_nomogram"]
            row_dict["in_hospital_risk_category"] = result["in_hospital_risk_category"]
            row_dict["model_limitations"] = result["model_limitations"]
            row_dict["treatment_recommendation"] = result["treatment_recommendation"]
            out_rows.append(row_dict)
        except (ValueError, KeyError, TypeError) as e:
            print(f"Error: invalid input on CSV record {i}: {e}", file=sys.stderr)
            return 1

    with open(args.output, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Processed {len(out_rows)}/{len(rows)} records -> {args.output}")
    return 0


def cmd_audit(args):
    """Run an audit task through the supervisor."""
    try:
        from agents.supervisor import SystemSupervisor
        from agents.models import SystemTaskPayload
        from agents.base import AuditLogger

        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.task_id,
            primary_metric=10.0,
            secondary_metric=5.0,
            status_descriptor="NOMINAL",
        )
        dossier = supervisor.process_task(payload)
        print(json.dumps(dossier.to_dict(), indent=2, default=str))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_chat(args):
    """Query the supervisory chat assistant."""
    try:
        from agents.supervisor import SystemSupervisor

        supervisor = SystemSupervisor(model_provider="mock")
        query = " ".join(args.query)
        response = supervisor.query_supervisory_chat(query)
        print(response)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_verify_audit(args):
    """Verify the integrity of the HMAC audit trail."""
    from agents.base import AuditLogger

    verified = AuditLogger.verify_integrity()
    trail_len = len(AuditLogger.get_trail())
    print(f"Audit trail entries: {trail_len}")
    print(f"Integrity verified: {verified}")
    return 0 if verified else 1


def _parse_bool(val: str) -> bool:
    """Parse a Boolean without silently converting malformed input to false."""
    normalized = str(val).strip().lower()
    if normalized in ("true", "yes", "1"):
        return True
    if normalized in ("false", "no", "0", ""):
        return False
    raise ValueError(f"Invalid boolean value: {val!r}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="grace-acs-risk-calculator",
        description="GRACE original 2003 in-hospital point score",
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

    # --- audit ---
    p_audit = subparsers.add_parser(
        "audit",
        help="Run an audit task through the supervisor",
    )
    p_audit.add_argument("--task-id", required=True, help="Task identifier")
    p_audit.set_defaults(func=cmd_audit)

    # --- chat ---
    p_chat = subparsers.add_parser(
        "chat",
        help="Query the supervisory chat assistant",
    )
    p_chat.add_argument("query", nargs="+", help="Query text")
    p_chat.set_defaults(func=cmd_chat)

    # --- serve ---
    p_serve = subparsers.add_parser("serve", help="Serve the web UI and API")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.set_defaults(func=cmd_serve)

    # --- verify-audit ---
    p_verify = subparsers.add_parser(
        "verify-audit",
        help="Verify the integrity of the HMAC audit trail",
    )
    p_verify.set_defaults(func=cmd_verify_audit)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, KeyError, TypeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
