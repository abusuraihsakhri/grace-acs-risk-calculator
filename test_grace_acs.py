"""Public compatibility API tests using actual GRACE input variables."""
import csv
import pytest

from grace_acs import calculate_metrics, process_batch


def test_grace_acs_single():
    result = calculate_metrics(
        age=65, heart_rate=80, systolic_bp=130, creatinine=1.0, killip_class=1
    )
    assert result["score"] == result["grace_score"] == 108
    assert result["classification"] == "Low"
    assert result["grace2_in_hospital_mortality_pct"] is None


def test_grace_acs_rejects_generic_values():
    with pytest.raises(ValueError, match="Missing required GRACE"):
        calculate_metrics(v1=12.0, v2=4.0)


def test_grace_acs_batch(tmp_path):
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text(
        "age,heart_rate,systolic_bp,creatinine,killip_class\n"
        "65,80,130,1,1\n"
        "67,96,128,1.1,1\n", encoding="utf-8"
    )
    process_batch(str(csv_in), str(csv_out))
    with csv_out.open(newline="",encoding="utf-8") as f:
        results=list(csv.DictReader(f))
    assert [r["grace_score"] for r in results] == ["108", "114"]


def test_grace_acs_batch_rejects_missing_fields(tmp_path):
    csv_in = tmp_path / "in.csv"
    csv_in.write_text("v1,v2\n12,4\n",encoding="utf-8")
    with pytest.raises(ValueError,match="CSV requires"):
        process_batch(str(csv_in), str(tmp_path / "out.csv"))
