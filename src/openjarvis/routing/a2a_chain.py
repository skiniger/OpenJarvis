"""A2A Chain — sequential multi-agent pipelines.

A chain defines an ordered list of agents where the output of step N becomes
(part of) the input for step N+1.  This enables complex workflows such as
``bavaria_booking → legal_assistant`` (book a room, then have legal review
the terms) without manual intervention.

Usage::

    from openjarvis.routing.a2a_chain import A2AChain, ChainStep

    chain = A2AChain(
        steps=[
            ChainStep(agent_id="bavaria_booking"),
            ChainStep(
                agent_id="legal_assistant",
                input_template="Prüfe rechtlich: {previous}",
            ),
        ],
        engine=engine,
        model="qwen3.5:4b",
    )
    result = chain.run("Neue Buchung für Müller, 2 Nächte")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from openjarvis.agents._stubs import AgentContext, AgentResult
from openjarvis.core.events import EventBus
from openjarvis.core.registry import AgentRegistry
from openjarvis.engine._stubs import InferenceEngine
from openjarvis.tools.agent_delegate import AgentDelegateTool

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ChainStep:
    """A single node in an A2A pipeline.

    *agent_id* identifies the worker.
    *input_template* controls how the step's query is built from the
    original user input and the previous step's output.

    Template variables:
    - ``{input}``      → the original query passed to ``A2AChain.run()``
    - ``{previous}``   → the content returned by the immediately preceding step
    """

    agent_id: str
    input_template: str = "{input}"


class A2AChain:
    """Sequential multi-agent pipeline.

    Parameters
    ----------
    steps:
        Ordered list of :class:`ChainStep`.
    engine:
        Shared inference engine handed to every sub-agent.
    model:
        Shared model name.
    bus:
        Optional event bus.
    temperature, max_tokens:
        Generation defaults forwarded to each sub-agent.
    capability_policy:
        Optional RBAC policy forwarded to each sub-agent.
    """

    def __init__(
        self,
        steps: List[ChainStep],
        engine: InferenceEngine,
        model: str,
        *,
        bus: Optional[EventBus] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        capability_policy: Optional[Any] = None,
    ) -> None:
        if not steps:
            raise ValueError("A2AChain requires at least one step.")
        for s in steps:
            if not AgentRegistry.contains(s.agent_id):
                raise ValueError(
                    f"Agent '{s.agent_id}' is not registered."
                )
        self._steps = steps
        self._delegate = AgentDelegateTool(
            engine=engine,
            model=model,
            bus=bus,
            temperature=temperature,
            max_tokens=max_tokens,
            capability_policy=capability_policy,
        )

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self, initial_query: str) -> AgentResult:
        """Execute the full pipeline and return the final result."""
        previous = ""
        all_tool_results: List[Any] = []
        total_turns = 0
        step_results: List[Dict[str, Any]] = []

        for idx, step in enumerate(self._steps, start=1):
            query = self._render_template(
                step.input_template,
                initial_query,
                previous,
            )
            logger.info(
                "a2a step %d/%d → %s (query=%.60s...)",
                idx,
                len(self._steps),
                step.agent_id,
                query,
            )

            tool_res = self._delegate.execute(
                agent_id=step.agent_id,
                query=query,
                context=previous,
            )

            if not tool_res.success:
                logger.error(
                    "a2a step %d failed: %s", idx, tool_res.content
                )
                return AgentResult(
                    content=tool_res.content,
                    tool_results=all_tool_results,
                    turns=total_turns,
                    metadata={
                        "chain_failed_at_step": idx,
                        "chain_failed_agent": step.agent_id,
                        "step_results": step_results,
                    },
                )

            previous = str(tool_res.content)
            total_turns += tool_res.metadata.get("sub_turns", 1)
            all_tool_results.append(tool_res)
            step_results.append(
                {
                    "step": idx,
                    "agent": step.agent_id,
                    "output": previous,
                }
            )

        return AgentResult(
            content=previous,
            tool_results=all_tool_results,
            turns=total_turns,
            metadata={
                "chain_steps": len(self._steps),
                "step_results": step_results,
            },
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _render_template(
        template: str,
        initial_query: str,
        previous_result: str,
    ) -> str:
        """Replace ``{input}`` and ``{previous}`` in *template*."""
        text = template.replace("{input}", initial_query)
        text = text.replace("{previous}", previous_result)
        return text

    @classmethod
    def from_string(
        cls,
        chain_spec: str,
        engine: InferenceEngine,
        model: str,
        **kwargs: Any,
    ) -> "A2AChain":
        """Parse a comma-separated chain spec into an :class:`A2AChain`.

        Spec format::

            agent_id1[> prompt],agent_id2[> prompt],...

        Examples::

            bavaria_booking,legal_assistant
            bavaria_booking,legal_assistant>Prüfe: {previous}
        """
        steps: List[ChainStep] = []
        for part in chain_spec.split(","):
            part = part.strip()
            if not part:
                continue
            if ">" in part:
                agent_id, tmpl = part.split(">", 1)
                steps.append(
                    ChainStep(
                        agent_id=agent_id.strip(),
                        input_template=tmpl.strip(),
                    )
                )
            else:
                steps.append(ChainStep(agent_id=part))
        return cls(steps, engine, model, **kwargs)


__all__ = ["A2AChain", "ChainStep"]
