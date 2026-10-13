"""
FastAPI REST API Server for Grace Acs Risk Calculator.
"""
from typing import Dict, Any, List
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from pydantic import Field, StrictBool, StrictInt
from grace import calculate_grace_score
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Grace Acs Risk Calculator API",
    description="Original GRACE 2003 in-hospital score and legacy audit demo",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str




class GraceRequest(BaseModel):
    """Presentation inputs. This endpoint does not accept patient identifiers."""
    age: StrictInt = Field(ge=18, le=120)
    heart_rate: StrictInt = Field(ge=20, le=300)
    systolic_bp: StrictInt = Field(ge=50, le=300)
    creatinine: float = Field(ge=0.1, le=20.0, allow_inf_nan=False)
    killip_class: StrictInt = Field(ge=1, le=4)
    cardiac_arrest: StrictBool = False
    st_deviation: StrictBool = False
    elevated_markers: StrictBool = False


@app.post("/api/grace")
def api_grace(payload: GraceRequest):
    """Return the 2003 point score, not an invented GRACE 2.0 risk."""
    try:
        return calculate_grace_score(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "grace-acs-risk-calculator", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


# Mount after API routes so /health, /metrics and /api/... remain accessible.
app.mount("/", StaticFiles(directory=str(Path(__file__).resolve().parents[1] / "docs"), html=True), name="site")
