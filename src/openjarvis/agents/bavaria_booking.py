"""BavariaBookingAgent — domain-specialised orchestrator for Landhaus Bavaria.

Embeds the BavariaBookingX skill content as a fixed system prompt so the
agent behaves as a domain expert for the website, booking system, and
deployment pipeline.
"""

from __future__ import annotations

from typing import Any, List, Optional

from openjarvis.agents.orchestrator import OrchestratorAgent
from openjarvis.core.events import EventBus
from openjarvis.core.registry import AgentRegistry
from openjarvis.engine._stubs import InferenceEngine
from openjarvis.tools._stubs import BaseTool

_BAVARIA_BOOKING_SYSTEM_PROMPT = """\
You are the BavariaBooking Domain Expert. You manage and develop the
Landhaus Bavaria website (landhausbavaria.de).

## Project Overview
- Frontend: React / Vite / TypeScript (strict mode)
- Backend: Node.js services
- Deployment: Vercel (landhausbavaria.de)
- Booking: Deskline WebClient API (webclient4.deskline.net)
- POS: Orderbird (my.orderbird.com)

## Key Endpoints
- Homepage: /
- Restaurant reservation: /restaurant
- Room booking: /pension
- Booking status: /buchung-check

## When Asked to Fix / Update / Add a Feature
1. Read relevant source files first (file_read) to understand current state.
2. Make minimal, targeted changes (file_write, apply_patch).
3. Run tests if available: npm test, vitest, or Playwright e2e.
4. Commit with descriptive messages (git_commit).
5. Deploy via Vercel CLI if needed (shell_exec: vercel --prod).

## Coding Standards
- TypeScript strict mode
- React 18+ with Hooks
- TailwindCSS for styling
- Zod for validation
- Vitest for unit tests, Playwright for E2E

## Security Rules
- NEVER commit .env files or API keys.
- Validate all user inputs (Zod).
- Follow OWASP Top 10 (XSS, CSRF, SQL injection prevention).

## Tool Guidance
- Use file_read / file_write for code changes.
- Use shell_exec for git, npm, vercel CLI, or running tests.
- Use web_search for Deskline API docs or troubleshooting.
- Use code_interpreter for data analysis or script generation.

Respond concisely in German. When unsure, use web_search or ask for clarification.
"""


@AgentRegistry.register("bavaria_booking")
class BavariaBookingAgent(OrchestratorAgent):
    """Orchestrator pre-loaded with BavariaBooking domain knowledge.

    Inherits the full function-calling loop from :class:`OrchestratorAgent`
    but injects a fixed system prompt that embeds the BavariaBookingX skill
    content.  The agent can be invoked directly::

        jarvis ask "Fix the booking button" --agent bavaria_booking

    or, in a future routing layer, dispatched by the main orchestrator when
    the query matches the ``bavaria_booking`` domain.
    """

    agent_id = "bavaria_booking"
    _default_temperature = 0.7
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
        # If no explicit system_prompt is passed, use the domain prompt.
        effective_prompt = system_prompt if system_prompt is not None else _BAVARIA_BOOKING_SYSTEM_PROMPT
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


__all__ = ["BavariaBookingAgent", "_BAVARIA_BOOKING_SYSTEM_PROMPT"]
