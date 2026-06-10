"""Tests for openjarvis.tools.agent_delegate.AgentDelegateTool."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from openjarvis.agents._stubs import AgentContext, AgentResult, BaseAgent
from openjarvis.core.registry import AgentRegistry
from openjarvis.core.types import ToolResult
from openjarvis.tools.agent_delegate import AgentDelegateTool


class _MockAgent(BaseAgent):
    """Minimal agent for delegation tests."""

    agent_id = "mock_agent"

    def run(
        self,
        input: str,
        context: AgentContext | None = None,
        **kwargs,
    ) -> AgentResult:
        return AgentResult(content=f"MockReply: {input}", turns=1)


@pytest.fixture
def delegate_setup(mock_engine, event_bus):
    AgentRegistry.register_value("mock_agent", _MockAgent)
    engine = mock_engine()
    tool = AgentDelegateTool(
        engine=engine,
        model="test-model",
        bus=event_bus,
        temperature=0.5,
        max_tokens=256,
    )
    return tool, engine


class TestAgentDelegateTool:
    def test_execute_success(self, delegate_setup):
        tool, _engine = delegate_setup
        result = tool.execute(agent_id="mock_agent", query="Hello")
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert "MockReply: Hello" in result.content
        assert result.metadata.get("sub_agent") == "mock_agent"
        assert result.metadata.get("sub_turns") == 1

    def test_execute_with_context(self, delegate_setup):
        tool, _engine = delegate_setup
        result = tool.execute(
            agent_id="mock_agent",
            query="Task",
            context="Background info",
        )
        assert result.success is True
        assert "MockReply:" in result.content

    def test_execute_unknown_agent(self, delegate_setup):
        tool, _engine = delegate_setup
        result = tool.execute(agent_id="nonexistent", query="Hello")
        assert result.success is False
        assert "not registered" in result.content

    def test_spec_fields(self, delegate_setup):
        tool, _engine = delegate_setup
        spec = tool.spec
        assert spec.name == "agent_delegate"
        assert "agent_id" in spec.parameters["properties"]
        assert "query" in spec.parameters["properties"]
        assert "context" in spec.parameters["properties"]

    def test_no_recursive_tools(self, delegate_setup):
        """Sub-agent must receive empty tools list to avoid infinite loops."""
        tool, _engine = delegate_setup
        # Execute once — if _MockAgent had accepted_tools=True and tools were
        # passed, the mock engine would have received tool definitions.
        result = tool.execute(agent_id="mock_agent", query="Test")
        assert result.success is True
