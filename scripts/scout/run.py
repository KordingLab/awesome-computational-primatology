#!/usr/bin/env python3
"""Paper Scout orchestrator: fetch → dedup → prefilter → judge → enrich → propose.

Usage:
    python scripts/scout/run.py --since 2026-01-01 --dry-run   # default: print, no PR
    python scripts/scout/run.py --open                          # open a draft PR
"""

from __future__ import annotations

import argparse
import datetime as dt

import dedup
import enrich
import fetch
import judge
import prefilter
import propose
import state as state_mod
from config import DEFAULT_LOOKBACK_DAYS


def resolve_since(arg_since: str | None, state: dict) -> str:
    """Pick the fetch window start: explicit arg > last run > default lookback."""
    if arg_since:
        return arg_since
    if state.get("last_run"):
        return state["last_run"]
    return (dt.date.today() - dt.timedelta(days=DEFAULT_LOOKBACK_DAYS)).isoformat()


def main() -> None:
    """Run the scout pipeline and either print (dry-run) or open a draft PR."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=None, help="ISO date; default = last run or lookback")
    ap.add_argument("--top", type=int, default=25, help="how many ranked candidates to show")
    ap.add_argument("--open", action="store_true", help="open a draft PR (default: dry-run)")
    args = ap.parse_args()

    state = state_mod.load_state()
    since = resolve_since(args.since, state)
    index = dedup.load_index()

    raw = fetch.fetch_all(since)
    fresh = [c for c in raw if not state_mod.is_seen(state, c.work_key)]
    dedup.classify_all(fresh, index)

    skips = [c for c in fresh if c.classification == "SKIP"]
    updates = [c for c in fresh if c.classification == "UPDATE"]
    news = [c for c in fresh if c.classification == "NEW"]
    survivors = prefilter.prefilter(news)

    print(f"\nPaper Scout — candidates published since {since}")
    print(f"  FETCH    {len(raw)} works ({len(raw) - len(fresh)} already seen in prior runs)")
    print(f"  DEDUP    SKIP={len(skips)}  UPDATE={len(updates)}  NEW={len(news)}")
    print(f"  RULES    {len(survivors)} NEW candidates passed (primate AND method)\n")

    if updates:
        print("  UPDATE (published version of a listed entry):")
        for c in updates:
            print(f"    → {c.update_target}: {propose.make_url(c)}  [{c.match_confidence}]")
        print()

    keeps: list = []
    reviews: list = []
    rejects: list = []

    if not judge.judge_available():
        print("  ⚠ GROQ_API_KEY not set — skipping LLM judge. Showing prefilter ranking only.\n")
        for c in survivors[: args.top]:
            flag = "TANGENT?" if c.is_tangent else ""
            print(f"    {c.prefilter_score:.3f}  {c.date}  {flag:<8}  {c.title[:72]}")
        return

    to_judge = survivors[: args.top]  # cap LLM calls; prefilter already ranked
    judge.judge_all(to_judge)
    keeps = [c for c in to_judge if c.decision == "KEEP"]
    reviews = [c for c in to_judge if c.decision == "REVIEW"]
    rejects = [c for c in to_judge if c.decision == "REJECT"]
    enrich.enrich_all(keeps + reviews)

    print(f"  JUDGE    KEEP={len(keeps)}  REVIEW={len(reviews)}  REJECT={len(rejects)}\n")
    body = propose.build_pr_body(keeps, reviews, updates, rejects)

    if not args.open:
        print("----- DRAFT PR BODY (dry-run) -----\n")
        print(body)
        print("\n----- PROPOSED ROWS -----")
        for c in keeps:
            print(propose.make_row(c))
        return

    if not (keeps or updates):
        print("Nothing to propose — no PR opened.")
        return

    readme = propose.README_PATH.read_text(encoding="utf-8")
    readme = propose.insert_rows(readme, [propose.make_row(c) for c in keeps])
    by_name = {e.name: e for e in index}
    for c in updates:
        if c.update_target in by_name:
            readme = propose.apply_update(readme, by_name[c.update_target], c)
    propose.README_PATH.write_text(readme, encoding="utf-8")
    propose.regenerate_index()

    state_mod.mark_seen(state, [c.work_key for c in survivors + updates])
    state["last_run"] = dt.date.today().isoformat()
    state_mod.save_state(state)

    branch = f"scout/{dt.date.today().isoformat()}"
    propose.open_pr(branch, f"Paper Scout: {len(keeps)} additions, {len(updates)} updates", body)
    print(f"Opened draft PR from branch {branch}.")


if __name__ == "__main__":
    main()
