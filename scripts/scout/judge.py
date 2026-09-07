#!/usr/bin/env python3
"""LLM judge: score candidates against the rubric via a free open-weight model (Groq)."""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

from config import (
    DEFAULT_MODEL,
    FALLBACK_MODELS,
    GROQ_BASE_URL,
    KEEP_THRESHOLD,
    REVIEW_THRESHOLD,
)
from fetch import Candidate
from prompts import build_judge_messages


class ModelUnavailable(RuntimeError):
    """Raised when Groq reports the requested model does not exist (404: retired/renamed)."""


def judge_available() -> bool:
    """Return True if a judge API key is configured."""
    return bool(os.environ.get("GROQ_API_KEY"))


def model_chain(model: str | None = None) -> list[str]:
    """Ordered list of models to try: explicit arg > $SCOUT_MODEL > default, then fallbacks."""
    first = model or os.environ.get("SCOUT_MODEL") or DEFAULT_MODEL
    chain = [first] + [m for m in FALLBACK_MODELS if m != first]
    return chain


def parse_verdict(content: str) -> dict:
    """Parse the model's reply into a verdict dict (tolerant of stray prose).

    Args:
        content: Raw model text, ideally a JSON object.

    Returns:
        Dict with keys decision/score/reason/animal/topic_tags (best-effort).
    """
    m = re.search(r"\{.*\}", content, re.DOTALL)
    data = json.loads(m.group(0)) if m else {}
    decision = str(data.get("decision", "REJECT")).upper()
    if decision not in {"KEEP", "REVIEW", "REJECT"}:
        decision = "REVIEW"
    try:  # the LLM occasionally returns a non-numeric score
        score = float(data.get("score", 0.0))
    except (TypeError, ValueError):
        score = 0.0
    tags = data.get("topic_tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    return {
        "decision": decision,
        "score": score,
        "reason": str(data.get("reason", "")).strip(),
        "animal": str(data.get("animal", "N/A")).strip() or "N/A",
        "topic_tags": tags,
    }


def _call_groq(messages: list[dict], model: str) -> str:
    """POST chat messages to the Groq OpenAI-compatible endpoint; return content.

    Retries with exponential backoff on 429 (rate limit) and 5xx (Groq outage, e.g. the
    503 that killed the 2026-08-24 run). Raises ModelUnavailable on 404 so the caller can
    fall through to the next model in the chain.
    """
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
    ).encode()
    req = urllib.request.Request(
        f"{GROQ_BASE_URL}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
            "Content-Type": "application/json",
            # Groq's edge blocks the default Python-urllib User-Agent (403).
            "User-Agent": "awesome-computational-primatology-scout/1.0",
        },
    )
    attempts = 5
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = json.load(resp)
            return body["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                detail = exc.read().decode("utf-8", "replace")[:300]
                raise ModelUnavailable(f"Groq returned 404 for model {model!r}: {detail}") from exc
            transient = exc.code == 429 or exc.code >= 500
            if transient and attempt < attempts - 1:
                time.sleep(2**attempt)
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt < attempts - 1:
                time.sleep(2**attempt)
                continue
            raise
    raise RuntimeError("unreachable")  # pragma: no cover


def judge_candidate(candidate: Candidate, model: str | None = None) -> Candidate:
    """Judge one candidate, setting decision/score/reason/animal/topic_tags in place.

    Args:
        candidate: The paper to judge (mutated in place).
        model: Exact model to use. When None, the first model in `model_chain()` is used;
            use `judge_all` for automatic fallback across the chain.
    """
    model = model or model_chain()[0]
    messages = build_judge_messages(
        candidate.title, candidate.venue, candidate.date, candidate.abstract
    )
    verdict = parse_verdict(_call_groq(messages, model))
    candidate.decision = verdict["decision"]
    candidate.score = verdict["score"]
    candidate.reason = verdict["reason"]
    candidate.animal = verdict["animal"]
    candidate.topic_tags = verdict["topic_tags"]
    return candidate


def decision_from_score(score: float) -> str:
    """Map a numeric score to KEEP/REVIEW/REJECT using the configured thresholds."""
    if score >= KEEP_THRESHOLD:
        return "KEEP"
    if score >= REVIEW_THRESHOLD:
        return "REVIEW"
    return "REJECT"


def judge_all(candidates: list[Candidate], model: str | None = None) -> list[Candidate]:
    """Judge every candidate (sequential; volume is small). Returns the same list.

    If Groq reports the current model as gone (404), the remaining candidates are judged
    with the next model in the chain; only when every model is unavailable does it raise.
    """
    chain = model_chain(model)
    idx = 0
    for c in candidates:
        while True:
            try:
                judge_candidate(c, chain[idx])
                break
            except ModelUnavailable as exc:
                print(f"  ⚠ {exc}", file=sys.stderr)
                idx += 1
                if idx >= len(chain):
                    raise RuntimeError(
                        "No judge model available on Groq — every model in the chain returned "
                        f"404: {chain}. Check https://console.groq.com/docs/deprecations and "
                        "update DEFAULT_MODEL/FALLBACK_MODELS in scripts/scout/config.py "
                        "(or set SCOUT_MODEL)."
                    ) from exc
                print(f"  ⚠ falling back to judge model {chain[idx]!r}", file=sys.stderr)
        time.sleep(0.1)
    return candidates
