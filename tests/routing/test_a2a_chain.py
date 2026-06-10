"""Tests for openjarvis.routing.a2a_chain.A2AChain."""

from __future__ import annotations

import pytest

from openjarvis.agents._stubs import AgentContext, AgentResult, BaseAgent
from openjarvis.core.registry import AgentRegistry
from openjarvis.routing.a2a_chain import A2AChain, ChainStep


class _AgentAlpha(BaseAgent):
    agent_id = "alpha"

    def run(self, input: str, context: AgentContext | None = None, **kwargs) -> AgentResult:
        return AgentResult(content=f"Alpha processed: {input}", turns=1)


class _AgentBeta(BaseAgent):
    agent_id = "beta"

    def run(self, input: str, context: AgentContext | None = None, **kwargs) -> AgentResult:
        return AgentResult(content=f"Beta processed: {input}", turns=1)


@pytest.fixture
def chain_setup(mock_engine, event_bus):
    AgentRegistry.register_value("alpha", _AgentAlpha)
    AgentRegistry.register_value("beta", _AgentBeta)
    engine = mock_engine()
    return engine, event_bus


class TestA2AChain:
    def test_single_step(self, chain_setup):
        engine, bus = chain_setup
        chain = A2AChain(
            steps=[ChainStep(agent_id="alpha")],
            engine=engine,
            model="test-model",
            bus=bus,
        )
        result = chain.run("Hello")
        assert result.content == "Alpha processed: Hello"
        assert result.turns == 1
        assert result.metadata["chain_steps"] == 1

    def test_two_step_pipeline(self, chain_setup):
        engine, bus = chain_setup
        chain = A2AChain(
            steps=[
                ChainStep(agent_id="alpha"),
                ChainStep(agent_id="beta"),
            ],
            engine=engine,
            model="test-model",
            bus=bus,
        )
        result = chain.run("Hello")
        # Beta receives Alpha's output as input via {previous} if template used,
        # but default template is {input}, so Beta gets original "Hello"
        assert "Beta processed:" in result.content
        assert result.metadata["chain_steps"] == 2

    def test_template_with_previous(self, chain_setup):
        engine, bus = chain_setup
        chain = A2AChain(
            steps=[
                ChainStep(agent_id="alpha"),
                ChainStep(
                    agent_id="beta",
                    input_template="Follow-up: {previous}",
                ),
            ],
            engine=engine,
            model="test-model",
            bus=bus,
        )
        result = chain.run("Hello")
        # AgentDelegateTool prepends context as [Context]...[Task]
        assert "Beta processed:" in result.content
        assert "Follow-up: Alpha processed: Hello" in result.content
        assert result.metadata["chain_steps"] == 2

    def test_from_string_simple(self, chain_setup):
        engine, bus = chain_setup
        chain = A2AChain.from_string(
            "alpha,beta",
            engine,
            "test-model",
            bus=bus,
        )
        assert len(chain._steps) == 2
        assert chain._steps[0].agent_id == "alpha"
        assert chain._steps[1].agent_id == "beta"

    def test_from_string_with_template(self, chain_setup):
        engine, bus = chain_setup
        chain = A2AChain.from_string(
            "alpha,beta>Review: {previous}",
            engine,
            "test-model",
            bus=bus,
        )
        assert chain._steps[1].input_template == "Review: {previous}"

    def test_empty_steps_raises(self, chain_setup):
        engine, bus = chain_setup
        with pytest.raises(ValueError, match="at least one step"):
            A2AChain([], engine, "test-model", bus=bus)

    def test_unregistered_agent_raises(self, chain_setup):
        engine, bus = chain_setup
        with pytest.raises(ValueError, match="not registered"):
            A2AChain(
                [ChainStep(agent_id="ghost")],
                engine,
                "test-model",
                bus=bus,
            )

    def test_failure_mid_chain(self, chain_setup):
        """If a step fails, the chain stops and reports the failing step."""
        engine, bus = chain_setup

        class _FailingAgent(BaseAgent):
            agent_id = "failing"

            def run(self, input, context=None, **kwargs):
                raise RuntimeError("boom")

        AgentRegistry.register_value("failing", _FailingAgent)

        chain = A2AChain(
            steps=[
                ChainStep(agent_id="alpha"),
                ChainStep(agent_id="failing"),
            ],
            engine=engine,
            model="test-model",
            bus=bus,
        )
        result = chain.run("Hello")
        assert result.metadata.get("chain_failed_at_step") == 2
        assert "boom" in result.content
