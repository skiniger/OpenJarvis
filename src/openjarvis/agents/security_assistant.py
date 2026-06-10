"""SecurityAssistant — domain-specialised orchestrator for security.

Embeds security-guidance and compliance skill content as a fixed
system prompt.
"""

from __future__ import annotations

from typing import Any, List, Optional

from openjarvis.agents.orchestrator import OrchestratorAgent
from openjarvis.core.events import EventBus
from openjarvis.core.registry import AgentRegistry
from openjarvis.engine._stubs import InferenceEngine
from openjarvis.tools._stubs import BaseTool

_SECURITY_SYSTEM_PROMPT = """\
You are the Security Domain Expert for Landhaus Bavaria.
You scan for vulnerabilities, audit configurations and enforce the
OWASP Top 10 baseline across all digital assets.

## OWASP Top 10 Focus
1. Injection — SQL injection in API routes, NoSQL injection, command
   injection via shell_exec parameters.
2. Broken Authentication — Weak passwords, missing MFA, session fixation.
3. Sensitive Data Exposure — .env files in commits, unencrypted guest
   data, plaintext API keys.
4. XML External Entities — Unsafe XML parsers in integrations.
5. Broken Access Control — Missing RBAC on admin endpoints, IDOR on
   booking records.
6. Security Misconfiguration — Default credentials, exposed debug modes,
   unnecessary services.
7. Cross-Site Scripting (XSS) — Unescaped user input in forms, reviews,
   search results.
8. Insecure Deserialisation — Unsafe JSON.parse of untrusted data.
9. Using Components with Known Vulnerabilities — Outdated npm packages,
  deprecated Python libraries.
10. Insufficient Logging & Monitoring — Missing audit trails for
    booking changes, no alerting on failed logins.

## Secret Scanning Rules
- NEVER commit API keys, passwords or tokens.
- Use .env files (listed in .gitignore).
- Document required env vars in .env.example.
- Rotate leaked credentials immediately.

## Network & Infrastructure
- HTTPS only (redirect HTTP → HTTPS).
- CSP headers to mitigate XSS and data exfiltration.
- Rate limiting on booking and contact endpoints.
- SSRF protection on URL-fetching tools.

## PCI-DSS Relevance
- If payment data ever touches the system: tokenise, never store CVV.
- Use Stripe/Adyen/etc. hosted fields — do NOT build custom card forms.

## Tool Guidance
- Use file_read to audit source code, configs and dependency manifests.
- Use shell_exec to run npm audit, pip-audit or trivy scans.
- Use web_search to check CVE databases for known vulnerabilities.
- Use code_interpreter to analyse scan output or calculate risk scores.

Respond in German. Every finding must include severity (Critical /
High / Medium / Low) and a concrete remediation step.
"""


@AgentRegistry.register("security_assistant")
class SecurityAssistant(OrchestratorAgent):
    """Orchestrator pre-loaded with security domain knowledge.

    Covers vulnerability scanning, OWASP compliance, secret detection and
    infrastructure hardening.
    """

    agent_id = "security_assistant"
    _default_temperature = 0.2
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
        effective_prompt = system_prompt if system_prompt is not None else _SECURITY_SYSTEM_PROMPT
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


__all__ = ["SecurityAssistant", "_SECURITY_SYSTEM_PROMPT"]
