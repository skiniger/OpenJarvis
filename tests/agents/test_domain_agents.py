"""Tests for Domain Agents — legal, marketing, operations, security.

Each agent inherits OrchestratorAgent and embeds a fixed domain system
prompt.  Tests verify registration, prompt content and override behaviour.
"""

from __future__ import annotations

import sys

import pytest

from tests.agents.fake_engine import FakeEngine


def _import_fresh(agent_module: str) -> None:
    """Force re-import so @AgentRegistry.register runs after conftest clears registries."""
    sys.modules.pop(agent_module, None)
    __import__(agent_module)


# ───────────────────────────────────────────────────────────────
# Legal Assistant
# ───────────────────────────────────────────────────────────────


def test_legal_agent_registered():
    """legal_assistant must be discoverable in AgentRegistry."""
    _import_fresh("openjarvis.agents.legal_assistant")
    from openjarvis.core.registry import AgentRegistry

    assert AgentRegistry.contains("legal_assistant")
    assert AgentRegistry.get("legal_assistant").agent_id == "legal_assistant"


def test_legal_agent_prompt():
    """Default system prompt must contain legal domain keywords."""
    _import_fresh("openjarvis.agents.legal_assistant")
    from openjarvis.agents.legal_assistant import LegalAssistant

    engine = FakeEngine([{"content": "Done"}])
    agent = LegalAssistant(engine, "fake-model")
    prompt = agent._system_prompt

    assert "Landhaus Bavaria" in prompt
    assert "GRÜN" in prompt
    assert "GELB" in prompt
    assert "ORANGE" in prompt
    assert "ROT" in prompt
    assert "DSGVO" in prompt
    assert "GastG" in prompt
    assert "ArbZG" in prompt
    assert "EU AI-Act" in prompt
    assert "KMU-DE" in prompt


def test_legal_agent_override():
    """Explicit system_prompt must override the domain default."""
    _import_fresh("openjarvis.agents.legal_assistant")
    from openjarvis.agents.legal_assistant import LegalAssistant

    custom = "Generic legal bot."
    engine = FakeEngine([{"content": "Done"}])
    agent = LegalAssistant(engine, "fake-model", system_prompt=custom)

    assert agent._system_prompt == custom
    assert "GRÜN" not in agent._system_prompt


# ───────────────────────────────────────────────────────────────
# Marketing Assistant
# ───────────────────────────────────────────────────────────────


def test_marketing_agent_registered():
    """marketing_assistant must be discoverable in AgentRegistry."""
    _import_fresh("openjarvis.agents.marketing_assistant")
    from openjarvis.core.registry import AgentRegistry

    assert AgentRegistry.contains("marketing_assistant")
    assert AgentRegistry.get("marketing_assistant").agent_id == "marketing_assistant"


def test_marketing_agent_prompt():
    """Default system prompt must contain marketing domain keywords."""
    _import_fresh("openjarvis.agents.marketing_assistant")
    from openjarvis.agents.marketing_assistant import MarketingAssistant

    engine = FakeEngine([{"content": "Done"}])
    agent = MarketingAssistant(engine, "fake-model")
    prompt = agent._system_prompt

    assert "Landhaus Bavaria" in prompt
    assert "Bavarian" in prompt or "bayerisch" in prompt
    assert "Email Sequences" in prompt or "email" in prompt.lower()
    assert "Campaign Planning" in prompt or "campaign" in prompt.lower()
    assert "Price Indication Ordinance" in prompt or "Preisangabenverordnung" in prompt
    assert "Newsletter" in prompt


def test_marketing_agent_override():
    """Explicit system_prompt must override the domain default."""
    _import_fresh("openjarvis.agents.marketing_assistant")
    from openjarvis.agents.marketing_assistant import MarketingAssistant

    custom = "Generic marketer."
    engine = FakeEngine([{"content": "Done"}])
    agent = MarketingAssistant(engine, "fake-model", system_prompt=custom)

    assert agent._system_prompt == custom
    assert "Bavarian" not in agent._system_prompt


# ───────────────────────────────────────────────────────────────
# Operations Assistant
# ───────────────────────────────────────────────────────────────


def test_operations_agent_registered():
    """operations_assistant must be discoverable in AgentRegistry."""
    _import_fresh("openjarvis.agents.operations_assistant")
    from openjarvis.core.registry import AgentRegistry

    assert AgentRegistry.contains("operations_assistant")
    assert AgentRegistry.get("operations_assistant").agent_id == "operations_assistant"


def test_operations_agent_prompt():
    """Default system prompt must contain operations domain keywords."""
    _import_fresh("openjarvis.agents.operations_assistant")
    from openjarvis.agents.operations_assistant import OperationsAssistant

    engine = FakeEngine([{"content": "Done"}])
    agent = OperationsAssistant(engine, "fake-model")
    prompt = agent._system_prompt

    assert "Landhaus Bavaria" in prompt
    assert "Ist-Soll" in prompt or "Ist-State" in prompt
    assert "Deskline" in prompt
    assert "Orderbird" in prompt
    assert "Housekeeping" in prompt or "housekeeping" in prompt.lower()
    assert "Automation" in prompt or "automation" in prompt.lower()
    assert "Prisma" in prompt or "iCal" in prompt


def test_operations_agent_override():
    """Explicit system_prompt must override the domain default."""
    _import_fresh("openjarvis.agents.operations_assistant")
    from openjarvis.agents.operations_assistant import OperationsAssistant

    custom = "Generic ops bot."
    engine = FakeEngine([{"content": "Done"}])
    agent = OperationsAssistant(engine, "fake-model", system_prompt=custom)

    assert agent._system_prompt == custom
    assert "Deskline" not in agent._system_prompt


# ───────────────────────────────────────────────────────────────
# Security Assistant
# ───────────────────────────────────────────────────────────────


def test_security_agent_registered():
    """security_assistant must be discoverable in AgentRegistry."""
    _import_fresh("openjarvis.agents.security_assistant")
    from openjarvis.core.registry import AgentRegistry

    assert AgentRegistry.contains("security_assistant")
    assert AgentRegistry.get("security_assistant").agent_id == "security_assistant"


def test_security_agent_prompt():
    """Default system prompt must contain security domain keywords."""
    _import_fresh("openjarvis.agents.security_assistant")
    from openjarvis.agents.security_assistant import SecurityAssistant

    engine = FakeEngine([{"content": "Done"}])
    agent = SecurityAssistant(engine, "fake-model")
    prompt = agent._system_prompt

    assert "OWASP" in prompt
    assert "Top 10" in prompt
    assert "Injection" in prompt
    assert "XSS" in prompt
    assert "Secrets" in prompt or "API keys" in prompt
    assert "HTTPS" in prompt
    assert "PCI-DSS" in prompt or "payment" in prompt.lower()
    assert "CVE" in prompt or "vulnerability" in prompt.lower()


def test_security_agent_override():
    """Explicit system_prompt must override the domain default."""
    _import_fresh("openjarvis.agents.security_assistant")
    from openjarvis.agents.security_assistant import SecurityAssistant

    custom = "Generic security bot."
    engine = FakeEngine([{"content": "Done"}])
    agent = SecurityAssistant(engine, "fake-model", system_prompt=custom)

    assert agent._system_prompt == custom
    assert "OWASP" not in agent._system_prompt


# ───────────────────────────────────────────────────────────────
# Shared behaviour
# ───────────────────────────────────────────────────────────────


def test_all_inherit_orchestrator():
    """All domain agents must be subclasses of OrchestratorAgent."""
    _import_fresh("openjarvis.agents.legal_assistant")
    _import_fresh("openjarvis.agents.marketing_assistant")
    _import_fresh("openjarvis.agents.operations_assistant")
    _import_fresh("openjarvis.agents.security_assistant")

    from openjarvis.agents.legal_assistant import LegalAssistant
    from openjarvis.agents.marketing_assistant import MarketingAssistant
    from openjarvis.agents.operations_assistant import OperationsAssistant
    from openjarvis.agents.security_assistant import SecurityAssistant
    from openjarvis.agents.orchestrator import OrchestratorAgent

    for cls in (LegalAssistant, MarketingAssistant, OperationsAssistant, SecurityAssistant):
        assert issubclass(cls, OrchestratorAgent)
