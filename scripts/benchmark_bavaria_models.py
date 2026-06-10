#!/usr/bin/env python3
"""Bavaria-specific model benchmark — evaluates local Ollama models.

Usage:
    .venv/bin/python scripts/benchmark_bavaria_models.py
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import requests

OLLAMA_HOST = "http://localhost:11434"
TIMEOUT_SEC = 300

PROMPTS: list[dict] = [
    {
        "id": "pricing",
        "text": (
            "Wie viel kostet ein Doppelzimmer in der Hauptsaison "
            "im Landhaus Bavaria?"
        ),
        "expected_keywords": ["95", "euro", "hauptsaison"],
    },
    {
        "id": "legal",
        "text": (
            "Muss ein kleines Hotel in Deutschland einen "
            "Datenschutzbeauftragten benennen?"
        ),
        "expected_keywords": ["dsgvo", "datenschutz", "nicht"],
    },
    {
        "id": "marketing",
        "text": (
            "Schreibe einen Newsletter-Einleitungstext für "
            "eine Sommerkampagne im Bayerischen Wald."
        ),
        "expected_keywords": ["bayerischer", "wald", "sommer"],
    },
    {
        "id": "operations",
        "text": (
            "Wie oft sollte ein Hotelzimmer in einem "
            "3-Sterne-Haus mindestens gereinigt werden?"
        ),
        "expected_keywords": ["täglich", "reinigung", "zimmer"],
    },
    {
        "id": "security",
        "text": (
            "Welche OWASP-Top-10-Risiken sind für eine "
            "Next.js-Website besonders relevant?"
        ),
        "expected_keywords": ["xss", "injection", "csrf"],
    },
]

# Models available locally (verified via /api/tags)
MODELS: list[str] = [
    "gemma3:1b",
    "qwen3.5:0.8b",
]


@dataclass(frozen=True)
class BenchmarkResult:
    model: str
    prompt_id: str
    duration_sec: float
    tokens_per_sec: float
    content: str
    keyword_hits: int
    keyword_score: float


def _chat(model: str, prompt: str, max_tokens: int = 200) -> tuple[str, float, float]:
    """Call Ollama /api/chat and return (text, duration, tokens/sec)."""
    url = f"{OLLAMA_HOST}/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": 0.3},
    }
    start = time.perf_counter()
    resp = requests.post(url, json=payload, timeout=TIMEOUT_SEC)
    duration = time.perf_counter() - start
    resp.raise_for_status()
    data = resp.json()
    text = data.get("message", {}).get("content", "").strip()
    eval_count = data.get("eval_count", 0)
    tps = eval_count / duration if duration > 0 else 0.0
    return text, duration, tps


def _score_keywords(content: str, keywords: list[str]) -> tuple[int, float]:
    lowered = content.lower()
    hits = sum(1 for kw in keywords if kw.lower() in lowered)
    return hits, hits / len(keywords)


def main() -> None:
    results: list[BenchmarkResult] = []
    print(f"{'Model':<22} {'Prompt':<12} {'Dur(s)':<8} {'Tok/s':<8} {'Score'}")
    print("-" * 70)

    for model in MODELS:
        for p in PROMPTS:
            try:
                text, dur, tps = _chat(model, p["text"])
                hits, score = _score_keywords(text, p["expected_keywords"])
                results.append(
                    BenchmarkResult(
                        model=model,
                        prompt_id=p["id"],
                        duration_sec=dur,
                        tokens_per_sec=tps,
                        content=text[:300],
                        keyword_hits=hits,
                        keyword_score=score,
                    )
                )
                print(
                    f"{model:<22} {p['id']:<12} {dur:<8.2f} {tps:<8.1f} "
                    f"{hits}/{len(p['expected_keywords'])} ({score:.0%})"
                )
            except Exception as exc:
                print(
                    f"{model:<22} {p['id']:<12} ERROR: {exc}",
                    file=sys.stderr,
                )

    print("\n" + "=" * 70)
    print("Summary by model (avg keyword score, avg tok/s, avg duration)")
    print("-" * 70)
    for model in MODELS:
        model_results = [r for r in results if r.model == model]
        if not model_results:
            continue
        avg_score = sum(r.keyword_score for r in model_results) / len(model_results)
        avg_tps = sum(r.tokens_per_sec for r in model_results) / len(model_results)
        avg_dur = sum(r.duration_sec for r in model_results) / len(model_results)
        print(
            f"{model:<22} score={avg_score:.1%}  tps={avg_tps:>6.1f}  dur={avg_dur:>5.2f}s"
        )

    out_path = Path("scripts") / "benchmark_bavaria_results.json"
    out_path.write_text(
        json.dumps([asdict(r) for r in results], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
