"""
Deterministic mock adapter; external inference providers are not implemented.
"""
from typing import Dict, Any, Optional
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Grace Acs Risk Calculator"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return f"[{self.system_name} mock]: No external inference or clinical validation was performed. Query preview: {prompt[:60]!r}."


class LLMFactory:
    """Return the explicit mock; reject unsupported external providers."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Grace Acs Risk Calculator"):
        prov = str(provider).lower()
        if prov in ["mock", "deterministic", "test"]:
            return MockLLM(system_name)
        raise ValueError(
            f"Provider {provider!r} is not implemented. Only the explicit mock provider is available."
        )
