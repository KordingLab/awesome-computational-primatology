#!/usr/bin/env python3
"""Persisted scout state: last-run date and the set of already-seen works."""

from __future__ import annotations

import json

from config import STATE_PATH


def load_state() -> dict:
    """Load scout-state.json, or a fresh empty state if absent."""
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"last_run": "", "seen": []}


def save_state(state: dict) -> None:
    """Write scout-state.json (pretty-printed for clean diffs)."""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def is_seen(state: dict, work_key: str) -> bool:
    """Return True if this work was proposed in a prior run."""
    return work_key in set(state.get("seen", []))


def mark_seen(state: dict, work_keys: list[str]) -> dict:
    """Add work keys to the seen set (deduplicated)."""
    state["seen"] = sorted(set(state.get("seen", [])) | set(work_keys))
    return state
