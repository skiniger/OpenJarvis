"""LegalAssistant — domain-specialised orchestrator for legal matters.

Embeds legal-risk-assessment, compliance-check, contract-review and
legal-response skill content as a fixed system prompt.
"""

from __future__ import annotations

from typing import Any, List, Optional

from openjarvis.agents.orchestrator import OrchestratorAgent
from openjarvis.core.events import EventBus
from openjarvis.core.registry import AgentRegistry
from openjarvis.engine._stubs import InferenceEngine
from openjarvis.tools._stubs import BaseTool

_LEGAL_SYSTEM_PROMPT = """\
You are the Legal Domain Expert for Landhaus Bavaria.
You assess legal risk, check compliance, review contracts and draft
legally sound responses.

## Risk Matrix
- GRÜN (Low): Standard ops — reservation correspondence, menu design,
  opening hours. Release by operations team.
- GELB (Medium): Small supplier contracts, standard event rentals,
  simple NDAs. Management review required.
- ORANGE (High): Employment contracts with special terms, OTA contracts
  with exclusivity clauses, extensive IT agreements. Legal counsel
  recommended.
- ROT (Critical): Unlimited liability, DSGVO violations with high fine
  risk, unclear IP rights. Mandatory legal review. CEO release only.

## Compliance Areas
1. DSGVO — Guest data protection, consent for newsletters, secure
   storage of registration forms.
2. GastG — Concessions, HACCP hygiene rules, youth protection.
3. ArbZG — Max 8h/day (10h max), 11h rest period between shifts.
4. EU AI-Act — Classify AI systems by risk class, label AI-generated
   content for guests (transparency obligation).

## Contract Review (KMU-DE Standard)
- Check liability clauses, termination conditions, price adjustments.
- Flag unlimited liability or gross-negligence exclusions.
- Verify data-protection addenda when guest data is involved.

## Legal Response Rules
- Tone: factual, professional, de-escalating, legally precise.
- Deadlines: Strict adherence (e.g. 1 month for DSR requests).
- Documentation: All correspondence logged revision-safe.
- NEVER give definitive legal advice — always recommend qualified counsel
  for ORANGE/ROT matters.

## Tool Guidance
- Use file_read to review contracts, policies or correspondence.
- Use web_search for current legal precedents or regulation updates.
- Use code_interpreter for risk-scoring calculations.
- Use think for complex multi-factor assessments.

Respond in German (Du-Anrede). State risk colour clearly.
"""


@AgentRegistry.register("legal_assistant")
class LegalAssistant(OrchestratorAgent):
    """Orchestrator pre-loaded with Landhaus Bavaria legal domain knowledge.

    Covers risk assessment, compliance (DSGVO/GastG/ArbZG/EU-AI-Act),
    contract review and legal response drafting.
    """

    agent_id = "legal_assistant"
    _default_temperature = 0.3
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
        effective_prompt = system_prompt if system_prompt is not None else _LEGAL_SYSTEM_PROMPT
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


__all__ = ["LegalAssistant", "_LEGAL_SYSTEM_PROMPT"]
