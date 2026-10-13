"""Regression tests for audit integrity and conservative mock behavior."""
import pytest

from agents.base import AuditTrail, PHIGuard, SecurityException
from agents.llm_factory import LLMFactory, MockLLM
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor


def make_trail():
    return AuditTrail(secret_key="test-only-ephemeral-key-" + "X" * 40)


@pytest.mark.parametrize("field", [
    "audit_id", "timestamp", "actor", "actor_tier",
    "event_type", "payload_hash", "prev_hash", "current_hash",
])
def test_modified_audit_fields_invalidate_hmac(field):
    trail=make_trail()
    trail.log("operator","reviewer","EVENT",{"record":"nonidentifying"})
    trail.logs[0][field]="altered"
    assert not trail.verify_integrity()


def test_chain_break_detected():
    trail=make_trail()
    trail.log("operator","reviewer","EVENT",{"number":1})
    trail.log("operator","reviewer","EVENT",{"number":2})
    trail.logs[0]["current_hash"]="0"*64
    assert not trail.verify_integrity()


def test_audit_snapshot_cannot_edit_signed_state():
    trail=make_trail()
    trail.log("operator","reviewer","EVENT",{"number":1})
    snapshot=trail.get_trail()
    snapshot[0]["current_hash"]="f"*64
    assert trail.verify_integrity()


def test_guard_blocks_obvious_identifiers():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("MRN-994827")


def test_supervisor_checks_attributes_as_well_as_label():
    payload=SystemTaskPayload(
        task_id="K-12",target_identifier="K-12",primary_metric=0.1,
        attributes={"unsafe":"MRN-994827"}
    )
    with pytest.raises(SecurityException):
        SystemSupervisor(model_provider="mock").process_task(payload)


def test_mock_is_identified_and_unsupported_providers_fail():
    assert isinstance(LLMFactory.create("mock"),MockLLM)
    assert "No external inference" in MockLLM().invoke("Explain this example")
    with pytest.raises(ValueError,match="not implemented"):
        LLMFactory.create("openai")
