"""Regression tests for the original (2003) GRACE in-hospital model.

Point tables and nomogram anchors: Granger et al. Arch Intern Med. 2003.
DOI: 10.1001/archinte.163.19.2345
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from grace import (
    calculate_grace_score,
    describe_killip,
    format_result,
    _in_hospital_mortality,
    _lookup_bracket,
    _lookup_creatinine,
    _lookup_sbp,
    _grace2_mortality,
    _six_month_mortality,
    _nomogram_lookup,
    _AGE_TABLE,
    _HR_TABLE,
)

ROOT = Path(__file__).resolve().parent.parent
BASE = dict(age=65, heart_rate=80, systolic_bp=130, creatinine=1.0, killip_class=1)


@pytest.mark.parametrize("age,points", [
    (18,0),(29,0),(30,8),(39,8),(40,25),(49,25),(50,41),
    (59,41),(60,58),(69,58),(70,75),(79,75),(80,91),
    (89,91),(90,100),(120,100)])
def test_age_points(age, points):
    assert _lookup_bracket(age, _AGE_TABLE) == points


@pytest.mark.parametrize("rate,points", [
    (20,0),(49,0),(50,3),(69,3),(70,9),(89,9),
    (90,15),(109,15),(110,24),(149,24),(150,38),
    (199,38),(200,46),(300,46)])
def test_heart_rate_points(rate, points):
    assert _lookup_bracket(rate, _HR_TABLE) == points


@pytest.mark.parametrize("pressure,points", [
    (50,58),(79,58),(80,53),(99,53),(100,43),(119,43),
    (120,34),(139,34),(140,24),(159,24),(160,10),(199,10),
    (200,0),(300,0)])
def test_sbp_points(pressure, points):
    assert _lookup_sbp(pressure) == points


@pytest.mark.parametrize("cr,points", [
    (.1,1),(.39999,1),(.4,4),(.79999,4),(.8,7),(1.1999,7),
    (1.2,10),(1.5999,10),(1.6,13),(1.9999,13),(2.0,21),
    (3.9999,21),(4.0,28),(20.0,28)])
def test_creatinine_points(cr, points):
    assert _lookup_creatinine(cr) == points


@pytest.mark.parametrize("klass,points",[(1,0),(2,20),(3,39),(4,59)])
def test_killip_points(klass, points):
    assert calculate_grace_score(**{**BASE,"killip_class":klass})["killip_points"] == points


@pytest.mark.parametrize("flag,points_key,expected", [
    ("cardiac_arrest","cardiac_arrest_points",39),
    ("st_deviation","st_deviation_points",28),
    ("elevated_markers","elevated_markers_points",14),
])
def test_binary_factors(flag, points_key, expected):
    result = calculate_grace_score(**{**BASE,flag:True})
    assert result[points_key] == expected


def test_original_published_example():
    assert calculate_grace_score(**BASE)["grace_score"] == 108


def test_independent_worked_example():
    result = calculate_grace_score(
        age=67, heart_rate=96, systolic_bp=128, creatinine=1.1,
        killip_class=1, st_deviation=True, elevated_markers=True
    )
    assert result["grace_score"] == 156
    assert result["in_hospital_risk_category"] == "High"


def test_maximum_and_minimum_scores():
    minimum = calculate_grace_score(
        age=18, heart_rate=40, systolic_bp=250, creatinine=.1, killip_class=1)
    maximum = calculate_grace_score(
        age=99, heart_rate=250, systolic_bp=60, creatinine=6.0,
        killip_class=4, cardiac_arrest=True, st_deviation=True, elevated_markers=True)
    assert minimum["grace_score"] == 1
    assert maximum["grace_score"] == 372


@pytest.mark.parametrize("score,cat",[(0,"Low"),(108,"Low"),(109,"Intermediate"),(140,"Intermediate"),(141,"High"),(372,"High")])
def test_historical_esc_score_tiers(score, cat):
    assert _in_hospital_mortality(score)[1] == cat


@pytest.mark.parametrize("score,estimate", [
    (1,.2),(60,.2),(70,.3),(89,.4),(100,.8),(108,.8),
    (110,1.1),(140,2.9),(240,44),(250,52),(372,52)])
def test_published_nomogram_anchors(score, estimate):
    assert _nomogram_lookup(score)[0] == estimate


def test_no_unsupported_grace2_or_six_month_prediction():
    result = calculate_grace_score(**BASE)
    assert result["six_month_mortality_pct"] is None
    assert result["six_month_risk_category"] is None
    assert result["grace2_in_hospital_mortality_pct"] is None
    with pytest.raises(NotImplementedError):
        _grace2_mortality(108,-7.8188,.02677)
    with pytest.raises(NotImplementedError):
        _six_month_mortality(108)


@pytest.mark.parametrize("overrides", [
    {"age":17},{"age":121},{"age":60.2},{"age":True},
    {"heart_rate":19},{"heart_rate":301},{"heart_rate":float("nan")},
    {"systolic_bp":49},{"systolic_bp":301},
    {"creatinine":0},{"creatinine":20.1},{"creatinine":float("nan")},
    {"creatinine":float("inf")},{"creatinine":True},
    {"killip_class":0},{"killip_class":5},{"killip_class":2.3},
    {"cardiac_arrest":1},{"st_deviation":"yes"},{"elevated_markers":0},
])
def test_validation(overrides):
    with pytest.raises(ValueError):
        calculate_grace_score(**{**BASE,**overrides})


def test_describe_killip():
    assert "shock" in describe_killip(4).lower()
    with pytest.raises(ValueError):
        describe_killip(0)


def test_format_contains_scope_and_component_breakdown():
    report = format_result(calculate_grace_score(**BASE))
    assert "GRACE SCORE" in report
    assert "Six-month mortality: not calculated" in report
    assert "age_points: 58" in report


def cli(*args):
    return subprocess.run(
        [sys.executable, str(ROOT / "cli.py"), *args],
        cwd=ROOT, capture_output=True, text=True
    )


def test_cli_calculate_json():
    proc=cli("calculate","--age","65","--hr","80","--sbp","130",
             "--creatinine","1","--killip","1","--json")
    assert proc.returncode == 0, proc.stderr
    data=json.loads(proc.stdout)
    assert data["grace_score"]==108
    assert data["six_month_mortality_pct"] is None


def test_cli_killip():
    proc=cli("killip","--class","4")
    assert proc.returncode == 0
    assert "shock" in proc.stdout.lower()


def test_cli_batch(tmp_path):
    source = tmp_path / "input.csv"
    output = tmp_path / "results.csv"
    source.write_text(
        "age,heart_rate,systolic_bp,creatinine,killip_class,cardiac_arrest,st_deviation,elevated_markers\n"
        "65,80,130,1.0,1,false,false,false\n"
        "67,96,128,1.1,1,false,true,true\n", encoding="utf-8")
    proc=cli("batch","-i",str(source),"-o",str(output))
    assert proc.returncode == 0, proc.stderr
    with output.open(newline="",encoding="utf-8") as file:
        rows=list(csv.DictReader(file))
    assert [row["grace_score"] for row in rows]==["108","156"]
    assert "six_month_mortality_pct" not in rows[0]


def test_cli_rejects_invalid_boolean(tmp_path):
    source=tmp_path/"input.csv"
    output=tmp_path/"output.csv"
    source.write_text(
        "age,heart_rate,systolic_bp,creatinine,killip_class,st_deviation\n"
        "65,80,130,1,1,maybe\n",encoding="utf-8")
    proc=cli("batch","-i",str(source),"-o",str(output))
    assert proc.returncode != 0
    assert not output.exists()
