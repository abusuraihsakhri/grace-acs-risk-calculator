#!/usr/bin/env python3
"""
Comprehensive tests for the GRACE ACS Risk Score Calculator.

Covers:
  - Individual point-assignment components
  - Low-risk, intermediate-risk, and high-risk scenarios
  - Killip classification helper
  - In-hospital and 6-month mortality estimates (original bands + GRACE 2.0)
  - Clinical scenarios: STEMI, NSTEMI, unstable angina
  - Edge cases and input validation
  - CLI interface
"""

import json
import os
import sys
import subprocess
import tempfile

# Ensure the project root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from grace import (
    calculate_grace_score,
    describe_killip,
    format_result,
    _lookup_bracket,
    _lookup_sbp,
    _lookup_creatinine,
    _in_hospital_mortality,
    _six_month_mortality,
    _grace2_mortality,
    _treatment_recommendation,
    _AGE_TABLE,
    _HR_TABLE,
    _KILLIP_TABLE,
)


# ===================================================================
# Individual component tests
# ===================================================================

class TestAgePoints:
    def test_age_under_30(self):
        result = calculate_grace_score(
            age=25, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert result["age_points"] == 0

    def test_age_30_to_39(self):
        result = calculate_grace_score(
            age=35, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert result["age_points"] == 8

    def test_age_40_to_49(self):
        result = calculate_grace_score(
            age=45, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert result["age_points"] == 25

    def test_age_50_to_59(self):
        result = calculate_grace_score(
            age=55, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert result["age_points"] == 41

    def test_age_60_to_69(self):
        result = calculate_grace_score(
            age=65, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert result["age_points"] == 58

    def test_age_70_to_79(self):
        result = calculate_grace_score(
            age=75, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert result["age_points"] == 75

    def test_age_80_to_89(self):
        result = calculate_grace_score(
            age=85, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert result["age_points"] == 91

    def test_age_90_plus(self):
        result = calculate_grace_score(
            age=95, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert result["age_points"] == 100

    def test_age_exact_boundary_30(self):
        result = calculate_grace_score(
            age=30, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert result["age_points"] == 8

    def test_age_exact_boundary_90(self):
        result = calculate_grace_score(
            age=90, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        # Age >=90 gets 100 points per the GRACE spec
        assert result["age_points"] == 100


class TestHeartRatePoints:
    def test_hr_below_50(self):
        result = calculate_grace_score(
            age=50, heart_rate=45, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert result["hr_points"] == 0

    def test_hr_50_to_69(self):
        result = calculate_grace_score(
            age=50, heart_rate=60, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert result["hr_points"] == 5

    def test_hr_70_to_89(self):
        result = calculate_grace_score(
            age=50, heart_rate=80, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert result["hr_points"] == 9

    def test_hr_90_to_109(self):
        result = calculate_grace_score(
            age=50, heart_rate=100, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert result["hr_points"] == 15

    def test_hr_110_to_149(self):
        result = calculate_grace_score(
            age=50, heart_rate=130, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert result["hr_points"] == 24

    def test_hr_150_to_199(self):
        result = calculate_grace_score(
            age=50, heart_rate=170, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert result["hr_points"] == 38

    def test_hr_200_plus(self):
        result = calculate_grace_score(
            age=50, heart_rate=220, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert result["hr_points"] == 46


class TestSystolicBPPoints:
    def test_sbp_below_80(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=70, creatinine=1.0, killip_class=1
        )
        assert result["sbp_points"] == 63

    def test_sbp_80_to_99(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=90, creatinine=1.0, killip_class=1
        )
        assert result["sbp_points"] == 58

    def test_sbp_100_to_119(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=110, creatinine=1.0, killip_class=1
        )
        assert result["sbp_points"] == 47

    def test_sbp_120_to_139(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=130, creatinine=1.0, killip_class=1
        )
        assert result["sbp_points"] == 37

    def test_sbp_140_to_159(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=150, creatinine=1.0, killip_class=1
        )
        assert result["sbp_points"] == 26

    def test_sbp_160_to_199(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=180, creatinine=1.0, killip_class=1
        )
        assert result["sbp_points"] == 11

    def test_sbp_200_plus(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=210, creatinine=1.0, killip_class=1
        )
        assert result["sbp_points"] == 0


class TestCreatininePoints:
    def test_creatinine_low(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=0.3, killip_class=1
        )
        assert result["creatinine_points"] == 2

    def test_creatinine_normal_low(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=0.6, killip_class=1
        )
        assert result["creatinine_points"] == 5

    def test_creatinine_normal(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert result["creatinine_points"] == 8

    def test_creatinine_mildly_elevated(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=1.4, killip_class=1
        )
        assert result["creatinine_points"] == 11

    def test_creatinine_moderately_elevated(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=1.8, killip_class=1
        )
        assert result["creatinine_points"] == 14

    def test_creatinine_high(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=3.0, killip_class=1
        )
        assert result["creatinine_points"] == 23

    def test_creatinine_very_high(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=5.0, killip_class=1
        )
        assert result["creatinine_points"] == 31


class TestKillipPoints:
    def test_killip_1(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert result["killip_points"] == 0

    def test_killip_2(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=2
        )
        assert result["killip_points"] == 21

    def test_killip_3(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=3
        )
        assert result["killip_points"] == 43

    def test_killip_4(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=4
        )
        assert result["killip_points"] == 64


class TestBinaryRiskFactors:
    def test_no_binary_factors(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert result["cardiac_arrest_points"] == 0
        assert result["st_deviation_points"] == 0
        assert result["elevated_markers_points"] == 0

    def test_cardiac_arrest(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1,
            cardiac_arrest=True,
        )
        assert result["cardiac_arrest_points"] == 43

    def test_st_deviation(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1,
            st_deviation=True,
        )
        assert result["st_deviation_points"] == 30

    def test_elevated_markers(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1,
            elevated_markers=True,
        )
        assert result["elevated_markers_points"] == 15

    def test_all_binary_factors(self):
        result = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1,
            cardiac_arrest=True, st_deviation=True, elevated_markers=True,
        )
        assert result["cardiac_arrest_points"] == 43
        assert result["st_deviation_points"] == 30
        assert result["elevated_markers_points"] == 15


# ===================================================================
# Killip classification helper
# ===================================================================

class TestKillipDescription:
    def test_killip_1_description(self):
        desc = describe_killip(1)
        assert "No clinical signs" in desc

    def test_killip_2_description(self):
        desc = describe_killip(2)
        assert "heart failure" in desc.lower()

    def test_killip_3_description(self):
        desc = describe_killip(3)
        assert "pulmonary edema" in desc.lower() or "pulmonary oedema" in desc.lower()

    def test_killip_4_description(self):
        desc = describe_killip(4)
        assert "shock" in desc.lower()

    def test_killip_invalid(self):
        try:
            describe_killip(5)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_killip_zero(self):
        try:
            describe_killip(0)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


# ===================================================================
# Low-risk scenario (GRACE < 109)
# ===================================================================

class TestLowRiskScenario:
    """Young patient, normal vitals, no risk factors — should be low risk."""

    def test_low_risk_score(self):
        result = calculate_grace_score(
            age=42, heart_rate=72, systolic_bp=135, creatinine=0.9, killip_class=1
        )
        # Age 40-49: 25, HR 70-89: 9, SBP 120-139: 37, Creat 0.8-1.19: 8,
        # Killip I: 0, no binary factors
        # Total: 25 + 9 + 37 + 8 + 0 = 79
        assert result["grace_score"] == 79
        assert result["grace_score"] < 109

    def test_low_risk_in_hospital_mortality(self):
        result = calculate_grace_score(
            age=42, heart_rate=72, systolic_bp=135, creatinine=0.9, killip_class=1
        )
        assert result["in_hospital_risk_category"] in ("Low",)
        assert result["in_hospital_mortality_pct"] < 1.0

    def test_low_risk_six_month_mortality(self):
        result = calculate_grace_score(
            age=42, heart_rate=72, systolic_bp=135, creatinine=0.9, killip_class=1
        )
        assert result["six_month_risk_category"] in ("Low",)
        assert result["six_month_mortality_pct"] < 5.0

    def test_low_risk_treatment_conservative(self):
        result = calculate_grace_score(
            age=42, heart_rate=72, systolic_bp=135, creatinine=0.9, killip_class=1
        )
        assert "conservative" in result["treatment_recommendation"].lower()


# ===================================================================
# High-risk scenario (GRACE ≥ 140)
# ===================================================================

class TestHighRiskScenario:
    """Elderly patient with multiple risk factors — should be high risk."""

    def test_high_risk_score(self):
        result = calculate_grace_score(
            age=78, heart_rate=115, systolic_bp=85, creatinine=2.5, killip_class=3,
            st_deviation=True, elevated_markers=True,
        )
        # Age 70-79: 75, HR 110-149: 24, SBP 80-99: 58, Creat 2.0-3.99: 23,
        # Killip III: 43, ST: 30, Markers: 15
        # Total: 75 + 24 + 58 + 23 + 43 + 30 + 15 = 268
        assert result["grace_score"] == 268
        assert result["grace_score"] >= 140

    def test_high_risk_in_hospital_mortality(self):
        result = calculate_grace_score(
            age=78, heart_rate=115, systolic_bp=85, creatinine=2.5, killip_class=3,
            st_deviation=True, elevated_markers=True,
        )
        assert result["in_hospital_risk_category"] in ("High", "Very High")
        assert result["in_hospital_mortality_pct"] > 5.0

    def test_high_risk_six_month_mortality(self):
        result = calculate_grace_score(
            age=78, heart_rate=115, systolic_bp=85, creatinine=2.5, killip_class=3,
            st_deviation=True, elevated_markers=True,
        )
        assert result["six_month_risk_category"] in ("High", "Very High")
        assert result["six_month_mortality_pct"] > 10.0

    def test_high_risk_treatment_urgent(self):
        result = calculate_grace_score(
            age=78, heart_rate=115, systolic_bp=85, creatinine=2.5, killip_class=3,
            st_deviation=True, elevated_markers=True,
        )
        rec = result["treatment_recommendation"].lower()
        assert "invasive" in rec


# ===================================================================
# Clinical scenarios
# ===================================================================

class TestSTEMIScenario:
    """STEMI patient: 60-year-old male, tachycardic, hypotensive, elevated markers,
    ST elevation."""

    def test_stemi_score(self):
        result = calculate_grace_score(
            age=60, heart_rate=105, systolic_bp=100, creatinine=1.2,
            killip_class=2, st_deviation=True, elevated_markers=True,
        )
        # Age 60-69: 58, HR 90-109: 15, SBP 100-119: 47, Creat 1.2-1.59: 11,
        # Killip II: 21, ST: 30, Markers: 15
        # Total: 58 + 15 + 47 + 11 + 21 + 30 + 15 = 197
        assert result["grace_score"] == 197
        assert result["in_hospital_risk_category"] in ("High", "Very High")

    def test_stemi_mortality_elevated(self):
        result = calculate_grace_score(
            age=60, heart_rate=105, systolic_bp=100, creatinine=1.2,
            killip_class=2, st_deviation=True, elevated_markers=True,
        )
        assert result["in_hospital_mortality_pct"] > 2.0
        assert result["six_month_mortality_pct"] > 5.0


class TestNSTEMIScenario:
    """NSTEMI patient: 55-year-old, stable vitals, elevated troponin, no ST changes."""

    def test_nstemi_score(self):
        result = calculate_grace_score(
            age=55, heart_rate=78, systolic_bp=140, creatinine=1.0,
            killip_class=1, elevated_markers=True,
        )
        # Age 50-59: 41, HR 70-89: 9, SBP 140-159: 26, Creat 0.8-1.19: 8,
        # Killip I: 0, Markers: 15
        # Total: 41 + 9 + 26 + 8 + 0 + 15 = 99
        assert result["grace_score"] == 99
        assert result["grace_score"] < 109

    def test_nstemi_low_intermediate_risk(self):
        result = calculate_grace_score(
            age=55, heart_rate=78, systolic_bp=140, creatinine=1.0,
            killip_class=1, elevated_markers=True,
        )
        # Score 99: in-hospital is Low-Intermediate (90-119 band),
        # 6-month is Intermediate (89-118 band)
        assert result["in_hospital_risk_category"] in ("Low", "Low-Intermediate")
        assert result["six_month_risk_category"] in ("Low", "Intermediate")


class TestUnstableAnginaScenario:
    """Unstable angina: 50-year-old, normal vitals, no ST changes, negative markers."""

    def test_ua_score(self):
        result = calculate_grace_score(
            age=50, heart_rate=68, systolic_bp=145, creatinine=0.8,
            killip_class=1,
        )
        # Age 50-59: 41, HR 50-69: 5, SBP 140-159: 26, Creat 0.8-1.19: 8,
        # Killip I: 0
        # Total: 41 + 5 + 26 + 8 + 0 = 80
        assert result["grace_score"] == 80

    def test_ua_low_risk(self):
        result = calculate_grace_score(
            age=50, heart_rate=68, systolic_bp=145, creatinine=0.8,
            killip_class=1,
        )
        assert result["in_hospital_risk_category"] == "Low"
        assert result["six_month_risk_category"] == "Low"
        assert result["in_hospital_mortality_pct"] < 1.0


class TestCardiacArrestScenario:
    """Patient brought in after cardiac arrest — highest risk factor."""

    def test_arrest_score(self):
        result = calculate_grace_score(
            age=65, heart_rate=95, systolic_bp=90, creatinine=1.5,
            killip_class=4, cardiac_arrest=True, st_deviation=True,
            elevated_markers=True,
        )
        # Age 60-69: 58, HR 90-109: 15, SBP 80-99: 58, Creat 1.2-1.59: 11,
        # Killip IV: 64, Arrest: 43, ST: 30, Markers: 15
        # Total: 58 + 15 + 58 + 11 + 64 + 43 + 30 + 15 = 294
        assert result["grace_score"] == 294
        assert result["in_hospital_risk_category"] in ("High", "Very High")
        assert result["in_hospital_mortality_pct"] > 10.0


# ===================================================================
# Mortality estimates — original bands
# ===================================================================

class TestInHospitalMortalityBands:
    def test_very_low_score(self):
        range_str, cat = _in_hospital_mortality(50)
        assert range_str == "<0.2%"
        assert cat == "Low"

    def test_low_score(self):
        range_str, cat = _in_hospital_mortality(75)
        assert range_str == "0.2-0.4%"
        assert cat == "Low"

    def test_low_intermediate_score(self):
        range_str, cat = _in_hospital_mortality(100)
        assert range_str == "0.4-0.9%"
        assert cat == "Low-Intermediate"

    def test_intermediate_score(self):
        range_str, cat = _in_hospital_mortality(130)
        assert range_str == "0.9-2.3%"
        assert cat == "Intermediate"

    def test_intermediate_high_score(self):
        range_str, cat = _in_hospital_mortality(160)
        assert range_str == "2.3-5.1%"
        assert cat == "Intermediate-High"

    def test_high_score(self):
        range_str, cat = _in_hospital_mortality(190)
        assert range_str == "5.1-10%"
        assert cat == "High"

    def test_very_high_score(self):
        range_str, cat = _in_hospital_mortality(250)
        assert range_str == ">10%"
        assert cat == "Very High"


class TestSixMonthMortalityBands:
    def test_low_score(self):
        range_str, cat = _six_month_mortality(70)
        assert range_str == "<3%"
        assert cat == "Low"

    def test_intermediate_score(self):
        range_str, cat = _six_month_mortality(100)
        assert range_str == "3-8%"
        assert cat == "Intermediate"

    def test_high_score(self):
        range_str, cat = _six_month_mortality(130)
        assert range_str == "8-19%"
        assert cat == "High"

    def test_very_high_score(self):
        range_str, cat = _six_month_mortality(200)
        assert range_str == ">19%"
        assert cat == "Very High"


# ===================================================================
# GRACE 2.0 continuous mortality
# ===================================================================

class TestGrace2Mortality:
    def test_low_score_grace2_in_hospital(self):
        # Score 60 → ~0.2% in-hospital mortality with calibrated coefficients
        pct = _grace2_mortality(60, -7.8188, 0.02677)
        assert pct < 1.0

    def test_mid_score_grace2_in_hospital(self):
        # Score 150 → ~2.2% in-hospital mortality with calibrated coefficients
        pct = _grace2_mortality(150, -7.8188, 0.02677)
        assert 1.0 < pct < 10.0

    def test_high_score_grace2_in_hospital(self):
        pct = _grace2_mortality(250, -7.8188, 0.02677)
        assert pct > 10.0

    def test_grace2_monotonicity(self):
        """Higher GRACE score → higher mortality estimate."""
        low = _grace2_mortality(60, -5.3275, 0.02856)
        mid = _grace2_mortality(120, -5.3275, 0.02856)
        high = _grace2_mortality(200, -5.3275, 0.02856)
        assert low < mid < high

    def test_grace2_six_month_monotonicity(self):
        low = _grace2_mortality(60, -4.2530, 0.01972)
        mid = _grace2_mortality(120, -4.2530, 0.01972)
        high = _grace2_mortality(200, -4.2530, 0.01972)
        assert low < mid < high

    def test_grace2_in_hospital_present_in_result(self):
        result = calculate_grace_score(
            age=65, heart_rate=80, systolic_bp=130, creatinine=1.0, killip_class=1
        )
        assert "grace2_in_hospital_mortality_pct" in result
        assert "grace2_six_month_mortality_pct" in result
        assert isinstance(result["grace2_in_hospital_mortality_pct"], float)
        assert isinstance(result["grace2_six_month_mortality_pct"], float)


# ===================================================================
# Treatment recommendations
# ===================================================================

class TestTreatmentRecommendations:
    def test_low_risk_conservative(self):
        rec = _treatment_recommendation(80, 1)
        assert "conservative" in rec.lower()

    def test_intermediate_risk_early_invasive(self):
        rec = _treatment_recommendation(120, 1)
        assert "invasive" in rec.lower()

    def test_high_risk_early_invasive(self):
        rec = _treatment_recommendation(160, 2)
        assert "invasive" in rec.lower()

    def test_very_high_risk_killip_3_4(self):
        rec = _treatment_recommendation(200, 3)
        assert "urgent" in rec.lower() or "invasive" in rec.lower()

    def test_very_high_risk_killip_4(self):
        rec = _treatment_recommendation(250, 4)
        assert "mechanical" in rec.lower() or "circulatory" in rec.lower()


# ===================================================================
# Input validation
# ===================================================================

class TestInputValidation:
    def test_invalid_age_too_low(self):
        try:
            calculate_grace_score(
                age=10, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Age" in str(e)

    def test_invalid_age_too_high(self):
        try:
            calculate_grace_score(
                age=150, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Age" in str(e)

    def test_invalid_hr_too_low(self):
        try:
            calculate_grace_score(
                age=50, heart_rate=10, systolic_bp=120, creatinine=1.0, killip_class=1
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Heart rate" in str(e)

    def test_invalid_sbp_too_low(self):
        try:
            calculate_grace_score(
                age=50, heart_rate=70, systolic_bp=30, creatinine=1.0, killip_class=1
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Systolic" in str(e)

    def test_invalid_creatinine(self):
        try:
            calculate_grace_score(
                age=50, heart_rate=70, systolic_bp=120, creatinine=0.0, killip_class=1
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Creatinine" in str(e)

    def test_invalid_killip(self):
        try:
            calculate_grace_score(
                age=50, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=5
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Killip" in str(e)


# ===================================================================
# Score monotonicity
# ===================================================================

class TestScoreMonotonicity:
    def test_older_age_higher_score(self):
        young = calculate_grace_score(
            age=35, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        old = calculate_grace_score(
            age=85, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert old["grace_score"] > young["grace_score"]

    def test_higher_hr_higher_score(self):
        low_hr = calculate_grace_score(
            age=50, heart_rate=55, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        high_hr = calculate_grace_score(
            age=50, heart_rate=180, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        assert high_hr["grace_score"] > low_hr["grace_score"]

    def test_lower_bp_higher_score(self):
        high_bp = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=180, creatinine=1.0, killip_class=1
        )
        low_bp = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=75, creatinine=1.0, killip_class=1
        )
        assert low_bp["grace_score"] > high_bp["grace_score"]

    def test_higher_creatinine_higher_score(self):
        low_cr = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=0.5, killip_class=1
        )
        high_cr = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=4.5, killip_class=1
        )
        assert high_cr["grace_score"] > low_cr["grace_score"]

    def test_higher_killip_higher_score(self):
        k1 = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=1
        )
        k4 = calculate_grace_score(
            age=50, heart_rate=70, systolic_bp=120, creatinine=1.0, killip_class=4
        )
        assert k4["grace_score"] > k1["grace_score"]


# ===================================================================
# Format result
# ===================================================================

class TestFormatResult:
    def test_format_contains_score(self):
        result = calculate_grace_score(
            age=65, heart_rate=85, systolic_bp=130, creatinine=1.1, killip_class=1
        )
        text = format_result(result)
        assert "GRACE SCORE" in text
        assert str(result["grace_score"]) in text

    def test_format_contains_mortality(self):
        result = calculate_grace_score(
            age=65, heart_rate=85, systolic_bp=130, creatinine=1.1, killip_class=1
        )
        text = format_result(result)
        assert "mortality" in text.lower()

    def test_format_contains_treatment(self):
        result = calculate_grace_score(
            age=65, heart_rate=85, systolic_bp=130, creatinine=1.1, killip_class=1
        )
        text = format_result(result)
        assert "TREATMENT" in text


# ===================================================================
# CLI tests
# ===================================================================

class TestCLI:
    """Test the CLI by invoking it as a subprocess."""

    def _run_cli(self, *args):
        project_root = os.path.join(os.path.dirname(__file__), "..")
        cmd = [sys.executable, os.path.join(project_root, "cli.py")] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
        return result

    def test_calculate_basic(self):
        result = self._run_cli(
            "calculate", "--age", "65", "--hr", "85", "--sbp", "130",
            "--creatinine", "1.1", "--killip", "1"
        )
        assert result.returncode == 0
        assert "GRACE SCORE" in result.stdout

    def test_calculate_json(self):
        result = self._run_cli(
            "calculate", "--age", "65", "--hr", "85", "--sbp", "130",
            "--creatinine", "1.1", "--killip", "1", "--json"
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "grace_score" in data
        assert isinstance(data["grace_score"], int)

    def test_calculate_with_flags(self):
        result = self._run_cli(
            "calculate", "--age", "70", "--hr", "100", "--sbp", "90",
            "--creatinine", "2.0", "--killip", "3",
            "--st-deviation", "--elevated-markers"
        )
        assert result.returncode == 0
        assert "GRACE SCORE" in result.stdout

    def test_killip_helper(self):
        result = self._run_cli("killip", "--class", "2")
        assert result.returncode == 0
        assert "Killip Class 2" in result.stdout

    def test_batch_processing(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        ) as f:
            f.write("age,heart_rate,systolic_bp,creatinine,killip_class,cardiac_arrest,st_deviation,elevated_markers\n")
            f.write("65,85,130,1.1,1,false,false,false\n")
            f.write("78,115,85,2.5,3,false,true,true\n")
            tmp_in = f.name

        tmp_out = tmp_in.replace(".csv", "_out.csv")
        try:
            result = self._run_cli("batch", "-i", tmp_in, "-o", tmp_out)
            assert result.returncode == 0
            assert os.path.exists(tmp_out)
            with open(tmp_out, "r") as f:
                content = f.read()
            assert "grace_score" in content
            assert "in_hospital_risk_category" in content
        finally:
            os.unlink(tmp_in)
            if os.path.exists(tmp_out):
                os.unlink(tmp_out)

    def test_calculate_high_risk_json(self):
        result = self._run_cli(
            "calculate", "--age", "80", "--hr", "120", "--sbp", "80",
            "--creatinine", "3.0", "--killip", "4",
            "--cardiac-arrest", "--st-deviation", "--elevated-markers",
            "--json"
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["grace_score"] >= 200
        assert data["in_hospital_risk_category"] in ("High", "Very High")


# ===================================================================
# Specific score verification (manual calculation check)
# ===================================================================

class TestExactScoreVerification:
    """Verify specific scores against hand-calculated values."""

    def test_minimum_possible_score(self):
        """Youngest, healthiest patient possible."""
        result = calculate_grace_score(
            age=18, heart_rate=40, systolic_bp=250, creatinine=0.1, killip_class=1
        )
        # Age <30: 0, HR <50: 0, SBP ≥200: 0, Creat 0-0.39: 2, Killip I: 0
        assert result["grace_score"] == 2

    def test_maximum_realistic_score(self):
        """Oldest, sickest patient with all risk factors."""
        result = calculate_grace_score(
            age=99, heart_rate=250, systolic_bp=60, creatinine=6.0, killip_class=4,
            cardiac_arrest=True, st_deviation=True, elevated_markers=True,
        )
        # Age ≥90: 100, HR ≥200: 46, SBP <80: 63, Creat ≥4: 31, Killip IV: 64,
        # Arrest: 43, ST: 30, Markers: 15
        # Total: 100 + 46 + 63 + 31 + 64 + 43 + 30 + 15 = 392
        assert result["grace_score"] == 392

    def test_known_scenario_1(self):
        """62-year-old, HR 92, SBP 125, Cr 1.3, Killip I, no binary factors."""
        result = calculate_grace_score(
            age=62, heart_rate=92, systolic_bp=125, creatinine=1.3, killip_class=1
        )
        # Age 60-69: 58, HR 90-109: 15, SBP 120-139: 37, Creat 1.2-1.59: 11,
        # Killip I: 0
        # Total: 58 + 15 + 37 + 11 + 0 = 121
        assert result["grace_score"] == 121

    def test_known_scenario_2(self):
        """75-year-old, HR 110, SBP 95, Cr 2.0, Killip II, ST deviation."""
        result = calculate_grace_score(
            age=75, heart_rate=110, systolic_bp=95, creatinine=2.0, killip_class=2,
            st_deviation=True,
        )
        # Age 70-79: 75, HR 110-149: 24, SBP 80-99: 58, Creat 2.0-3.99: 23,
        # Killip II: 21, ST: 30
        # Total: 75 + 24 + 58 + 23 + 21 + 30 = 231
        assert result["grace_score"] == 231


# ===================================================================
# Return dict completeness
# ===================================================================

class TestResultCompleteness:
    def test_all_keys_present(self):
        result = calculate_grace_score(
            age=65, heart_rate=85, systolic_bp=130, creatinine=1.1, killip_class=2,
            cardiac_arrest=False, st_deviation=True, elevated_markers=True,
        )
        expected_keys = [
            "grace_score", "age_points", "hr_points", "sbp_points",
            "creatinine_points", "killip_points", "cardiac_arrest_points",
            "st_deviation_points", "elevated_markers_points",
            "in_hospital_mortality_pct", "in_hospital_mortality_range",
            "in_hospital_risk_category", "six_month_mortality_pct",
            "six_month_mortality_range", "six_month_risk_category",
            "grace2_in_hospital_mortality_pct", "grace2_six_month_mortality_pct",
            "killip_description", "treatment_recommendation",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_score_is_integer(self):
        result = calculate_grace_score(
            age=65, heart_rate=85, systolic_bp=130, creatinine=1.1, killip_class=1
        )
        assert isinstance(result["grace_score"], int)

    def test_mortality_is_float(self):
        result = calculate_grace_score(
            age=65, heart_rate=85, systolic_bp=130, creatinine=1.1, killip_class=1
        )
        assert isinstance(result["in_hospital_mortality_pct"], float)
        assert isinstance(result["six_month_mortality_pct"], float)
