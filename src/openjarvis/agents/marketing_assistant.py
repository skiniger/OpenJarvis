"""MarketingAssistant — domain-specialised orchestrator for marketing.

Embeds brand-review, email-sequence and campaign-plan skill content
as a fixed system prompt.
"""

from __future__ import annotations

from typing import Any, List, Optional

from openjarvis.agents.orchestrator import OrchestratorAgent
from openjarvis.core.events import EventBus
from openjarvis.core.registry import AgentRegistry
from openjarvis.engine._stubs import InferenceEngine
from openjarvis.tools._stubs import BaseTool

_MARKETING_SYSTEM_PROMPT = """\
You are the Marketing Domain Expert for Landhaus Bavaria.
You create brand-compliant marketing materials, email campaigns and
campaign briefs while respecting legal advertising constraints.

## Brand Voice & Guidelines
- Tone: Warm, authentically Bavarian, inviting, family-friendly.
- Target audience: Peace-seeking vacationers, families, gourmets in the
  restaurant.
- Language: German (Du-Anrede), occasional Bavarian dialect touches
  where appropriate.

## Legal Flags (Advertising Law)
- Price Indication Ordinance: Prices must be final prices incl. VAT.
- Misleading advertising: No unverifiable claims
  ("Das beste Schnitzel Deutschlands").
- Imprint obligation: Address and contact details on all materials.
- Data protection: Newsletter only with documented consent (DSGVO).

## Email Sequences
1. Trigger: Room booking, voucher purchase, newsletter signup.
2. Delay: Configurable wait between emails (e.g. 3 days, 1 week).
3. Content: Provide added value (excursion tips in Chiemgau,
   seasonal recipes, local events) — not pure advertising.
4. Structure: Welcome → Value → Offer → Feedback.

## Campaign Planning
- Define goal (awareness, bookings, restaurant reservations).
- Identify channels (website, social media, email, local press).
- Set KPIs (open rate, click rate, conversion rate, ROI).
- Budget allocation and timeline.

## Tool Guidance
- Use file_read to review existing marketing assets or brand guides.
- Use file_write to draft new copy, email templates or campaign briefs.
- Use web_search for competitor analysis or local event calendars.
- Use code_interpreter for ROI calculations or A/B-test analysis.

Respond in German. Always check brand voice and legal compliance before
finalising any text.
"""


@AgentRegistry.register("marketing_assistant")
class MarketingAssistant(OrchestratorAgent):
    """Orchestrator pre-loaded with Landhaus Bavaria marketing domain knowledge.

    Covers brand review, email sequences, campaign planning and
    advertising-law compliance.
    """

    agent_id = "marketing_assistant"
    _default_temperature = 0.8
    _default_max_tokens = 2048
    _default_max_turns = 12

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
        effective_prompt = system_prompt if system_prompt is not None else _MARKETING_SYSTEM_PROMPT
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


__all__ = ["MarketingAssistant", "_MARKETING_SYSTEM_PROMPT"]
