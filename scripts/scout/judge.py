#!/usr/bin/env python3
"""LLM judge: score candidates against the rubric via a free open-weight model (Groq)."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request

from config import DEFAULT_MODEL, GROQ_BASE_URL, KEEP_THRESHOLD, REVIEW_THRESHOLD
from fetch import Candidate
from prompts import build_judge_messages


def judge_available() -> bool:
    """Return True if a judge API key is configured."""
    return bool(os.environ.get("GROQ_API_KEY"))


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
    """POST chat messages to the Groq OpenAI-compatible endpoint; return content."""
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
    for attempt in range(4):  # exponential backoff on rate limit / transient errors
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = json.load(resp)
            return body["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            raise


def judge_candidate(candidate: Candidate, model: str | None = None) -> Candidate:
    """Judge one candidate, setting decision/score/reason/animal/topic_tags in place."""
    model = model or os.environ.get("SCOUT_MODEL", DEFAULT_MODEL)
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
    """Judge every candidate (sequential; volume is small). Returns the same list."""
    for c in candidates:
        judge_candidate(c, model)
        time.sleep(0.1)
    return candidates
