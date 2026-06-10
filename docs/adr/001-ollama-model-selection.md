# ADR 001: Ollama-Modellauswahl für Landhaus Bavaria Domain Agents

* **Status:** Accepted
* **Datum:** 2026-06-09
* **Autor:** OpenJarvis System

## Kontext

Die OpenJarvis Domain-Agent-Suite für Landhaus Bavaria benötigt ein lokal ausführbares LLM, das über Ollama auf der vorhandenen Hardware (Apple M2, 8 GB RAM) betrieben werden kann. Ziel war es, ein Modell zu finden, das:

1. Deutschsprachige Hospitality-Domain-Prompts versteht und beantwortet.
2. In einer vertretbaren Zeit (< 10 s) Antworten liefert.
3. Stabil läuft, ohne in Timeouts oder Swap zu laufen.
4. Für A2A-Chains (z. B. `bavaria_booking → legal_assistant`) brauchbare Zwischenoutputs erzeugt.

## Entscheidung

Für **Demo- und Testzwecke** wird **`gemma3:1b`** als einzige lokale Option akzeptiert.

Für **Produktion** wird die Nutzung einer **Cloud-API** (Anthropic Claude, OpenAI GPT) empfohlen, solange keine leistungsfähigere lokale Hardware (mindestens 32 GB RAM, Apple M4 Pro oder vergleichbar) verfügbar ist.

## Konsequenzen

### Positiv
- `gemma3:1b` läuft stabil auf M2/8 GB (~4 s pro Prompt, ~53 tok/s).
- Keyword-Score von ~53 % bei Bavaria-Prompts — ausreichend für Routing-Tests und A2A-Chain-Demos.
- A2A-Delegation (`AgentDelegateTool` → `A2AChain`) funktioniert end-to-end.
- Keine Cloud-Kosten oder Latenz für interne Tests.

### Negativ
- Output-Qualität bei `gemma3:1b` ist begrenzt; keine echte Rechts- oder Marketing-Expertise.
- `qwen3.5:0.8b` liefert leere Responses auf deutsche Prompts (0 % Keyword-Score).
- `llama3.2` und `qwen3.5:4b` sind auf 8 GB RAM nicht nutzbar (> 300 s Timeout).
- Für Gäste-facing Features (Buchungsassistent, Rechtstexte) ist Cloud-Qualität unverzichtbar.

## Alternativen

| Alternative | Ergebnis | Grund |
|-------------|----------|-------|
| `qwen3.5:0.8b` | Abgelehnt | Leere Outputs bei deutschen Hospitality-Prompts |
| `llama3.2` (3,2B) | Abgelehnt | Timeout / Swap auf M2/8 GB |
| `qwen3.5:4b` (4,7B) | Abgelehnt | Timeout / Swap auf M2/8 GB |
| Größere Hardware (M4 Pro/32 GB) | Offen | Wenn verfügbar, Re-Eval mit `llama3.2` / `qwen3.5:4b` |
| Cloud-API (Claude/GPT) | Empfohlen | Sofort produktionsreif, höchste Qualität |

## Links

- Benchmark-Script: `scripts/benchmark_bavaria_models.py`
- Benchmark-Ergebnisse: `scripts/benchmark_bavaria_results.json`
- A2A-Chain-Implementierung: `src/openjarvis/routing/a2a_chain.py`
- Agent-Router mit Keyword-Matching: `src/openjarvis/routing/agent_router.py`
- Memory-Eintrag: `[[openjarvis-model-eval-juni-2026]]`
