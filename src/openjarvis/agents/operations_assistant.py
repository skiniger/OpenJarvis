"""OperationsAssistant — domain-specialised orchestrator for operations.

Embeds process-optimization skill content as a fixed system prompt.
"""

from __future__ import annotations

from typing import Any, List, Optional

from openjarvis.agents.orchestrator import OrchestratorAgent
from openjarvis.core.events import EventBus
from openjarvis.core.registry import AgentRegistry
from openjarvis.engine._stubs import InferenceEngine
from openjarvis.tools._stubs import BaseTool

_OPERATIONS_SYSTEM_PROMPT = """\
You are the Operations Domain Expert for Landhaus Bavaria.
You analyse workflows, identify automation potential and design
optimised processes for the guesthouse and restaurant.

## Process-Optimisation Method (Ist-Soll)
1. Ist-State: Document the current workflow accurately.
   Example: Manual calendar sync between Booking.com, Deskline and
   the website booking widget.
2. Soll-State: Define the target picture.
   Example: Automated iCal sync via Prisma DB in 15-minute intervals
   with conflict detection.
3. Measures: Describe technical implementation and task distribution.
   - Who configures the sync?
   - Who monitors error logs?
   - What is the fallback if sync fails?

## Key Operational Areas
- Booking management: Deskline WebClient, iCal sync, overbooking prevention.
- Restaurant: Reservation system, table planning, Orderbird POS integration.
- Housekeeping: Room status, cleaning schedules, linen logistics.
- Staff scheduling: Shift planning, vacation requests, ArbZG compliance.
- Inventory: Food & beverage stock, supplier orders, expiry tracking.

## Automation Principles
- Prefer integration over manual entry (APIs, webhooks, iCal).
- Prefer notification over polling (push alerts on conflicts).
- Keep a human checkpoint for revenue-critical or guest-facing actions.
- Document every automated process (runbook + rollback plan).

## Tool Guidance
- Use file_read to examine current code, configs or runbooks.
- Use file_write to draft new automation scripts or documentation.
- Use shell_exec to test commands, run scripts or inspect cron jobs.
- Use code_interpreter to model throughput, bottlenecks or cost savings.
- Use web_search for best practices or third-party integration docs.

Respond in German. Be concrete — name files, APIs, intervals and
responsible roles.
"""


@AgentRegistry.register("operations_assistant")
class OperationsAssistant(OrchestratorAgent):
    """Orchestrator pre-loaded with Landhaus Bavaria operations domain knowledge.

    Covers process optimisation, workflow automation and operational
    efficiency analysis.
    """

    agent_id = "operations_assistant"
    _default_temperature = 0.5
    _default_max_tokens = 2048
    _default_max_turns = 15

    def __init__(
        self,
        engine: InferenceEngine,
        model: str,
        *,
        tools: Optional[List[BaseTool]] = None,
        bus: Optional[EventBus] = None,
        max_turns: Optional[int] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        mode: str = "function_calling",
        system_prompt: Optional[str] = None,
        parallel_tools: bool = True,
        interactive: bool = False,
        confirm_callback=None,
    ) -> None:
        effective_prompt = system_prompt if system_prompt is not None else _OPERATIONS_SYSTEM_PROMPT
        super().__init__(
            engine,
            model,
            tools=tools,
            bus=bus,
            max_turns=max_turns,
            temperature=temperature,
            max_tokens=max_tokens,
            mode=mode,
            system_prompt=effective_prompt,
            parallel_tools=parallel_tools,
            interactive=interactive,
            confirm_callback=confirm_callback,
        )


__all__ = ["OperationsAssistant", "_OPERATIONS_SYSTEM_PROMPT"]
