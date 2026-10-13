"""API smoke checks; API calculates only the historical in-hospital point score."""
import pytest
from fastapi.testclient import TestClient
from agents.api import app

client=TestClient(app)
EXAMPLE={"age":65,"heart_rate":80,"systolic_bp":130,
         "creatinine":1.0,"killip_class":1}


def test_api_calculate():
    response=client.post("/api/grace",json=EXAMPLE)
    assert response.status_code==200
    result=response.json()
    assert result["grace_score"]==108
    assert result["six_month_mortality_pct"] is None
    assert result["grace2_in_hospital_mortality_pct"] is None


@pytest.mark.parametrize("invalid", [
    {"age":65.5},{"age":17},{"creatinine":-1},
    {"killip_class":5},{"st_deviation":1}
])
def test_api_rejects_invalid_input(invalid):
    response=client.post("/api/grace",json={**EXAMPLE,**invalid})
    assert response.status_code==422


def test_api_index_and_javascript():
    response=client.get("/")
    assert response.status_code==200
    assert "GRACE ACS Risk Score" in response.text
    assert "/api/audit" not in response.text
    javascript=client.get("/calculator.js")
    assert javascript.status_code==200
    assert "GRACE" in javascript.text


def test_logs_private_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_AUDIT_LOGS",raising=False)
    response=client.get("/api/audit/logs")
    assert response.status_code==403
