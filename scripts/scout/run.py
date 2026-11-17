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
import preprints
import propose
import state as state_mod
from config import DEFAULT_LOOKBACK_DAYS

# Re-fetch this many days before the last run: OpenAlex often indexes a work days or
# weeks after its publication_date, so a window starting exactly at last_run misses
# late-indexed papers. The seen-set keeps the overlap from being re-judged.
WINDOW_OVERLAP_DAYS = 14


def resolve_since(arg_since: str | None, state: dict) -> str:
    """Pick the fetch window start: explicit arg > last run minus overlap > default lookback."""
    if arg_since:
        return arg_since
    if state.get("last_run"):
        last = dt.date.fromisoformat(state["last_run"])
        return (last - dt.timedelta(days=WINDOW_OVERLAP_DAYS)).isoformat()
    return (dt.date.today() - dt.timedelta(days=DEFAULT_LOOKBACK_DAYS)).isoformat()


def _published_as_update(p: preprints.PublishedVersion) -> fetch.Candidate:
    """Express a found published version as an UPDATE candidate for propose.apply_update."""
    return fetch.Candidate(
        source="preprint-check", title=p.title, abstract="", doi=p.doi, arxiv_id="",
        date=p.date, venue=p.venue, authors=[], classification="UPDATE",
        update_target=p.entry.name, match_confidence=p.confidence,
        reason=f"{p.evidence}; {p.venue}: “{p.title[:90]}”",
    )


def main() -> None:
    """Run the scout pipeline and either print (dry-run) or open a draft PR."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=None, help="ISO date; default = last run or lookback")
    ap.add_argument("--top", type=int, default=25, help="how many ranked candidates to show")
    ap.add_argument("--max-judge", type=int, default=50,
                    help="safety ceiling on how many ranked candidates to LLM-judge")
    ap.add_argument("--open", action="store_true", help="open a draft PR (default: dry-run)")
    args = ap.parse_args()

    state = state_mod.load_state()
    since = resolve_since(args.since, state)
    index = dedup.load_index()

    # Listed preprints that now have a published version (checked every run, all entries).
    published = preprints.find_all(index, skip_dois=set(state.get("seen", [])))
    pub_updates = [_published_as_update(p) for p in published if p.confidence == "high"]
    pub_maybe = [_published_as_update(p) for p in published if p.confidence != "high"]
    pub_dois = {p.doi for p in published}

    raw = fetch.fetch_all(since)
    # A published version found above is an UPDATE of its listed preprint, never a NEW row.
    fresh = [c for c in raw if not state_mod.is_seen(state, c.work_key) and c.doi not in pub_dois]
    dedup.classify_all(fresh, index)

    skips = [c for c in fresh if c.classification == "SKIP"]
    updates = pub_updates + [c for c in fresh if c.classification == "UPDATE"]
    news = [c for c in fresh if c.classification == "NEW"]
    survivors = prefilter.prefilter(news)

    print(f"\nPaper Scout — candidates published since {since}")
    print(f"  FETCH    {len(raw)} works ({len(raw) - len(fresh)} already seen in prior runs)")
    print(f"  DEDUP    SKIP={len(skips)}  UPDATE={len(updates)}  NEW={len(news)}")
    print(f"  RULES    {len(survivors)} NEW candidates passed (primate AND method)\n")

    if updates or pub_maybe:
        print("  UPDATE (published version of a listed entry):")
        for c in updates + pub_maybe:
            print(f"    → {c.update_target}: {propose.make_url(c)}  [{c.match_confidence}] {c.reason}")
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

    to_judge = survivors[: args.max_judge]  # safety ceiling on LLM calls (prefilter already ranked)
    judge.judge_all(to_judge)
    keeps = [c for c in to_judge if c.decision == "KEEP"]
    reviews = [c for c in to_judge if c.decision == "REVIEW"]
    rejects = [c for c in to_judge if c.decision == "REJECT"]
    enrich.enrich_all(keeps + reviews)

    print(f"  JUDGE    KEEP={len(keeps)}  REVIEW={len(reviews)}  REJECT={len(rejects)}\n")
    body = propose.build_pr_body(keeps, reviews, updates, rejects, maybe_updates=pub_maybe)

    if not args.open:
        print("----- DRAFT PR BODY (dry-run) -----\n")
        print(body)
        print("\n----- PROPOSED ROWS -----")
        for c in keeps:
            print(propose.make_row(c))
        return

    # Record what we judged (+ updates) even when nothing is proposed, so next week's
    # run neither re-judges it nor re-proposes it. Capped overflow is NOT recorded, so it
    # is reconsidered next run (the window overlap keeps it in range). The workflow
    # persists this file on the `scout-state` branch, independent of any PR.
    state_mod.mark_seen(state, [c.work_key for c in to_judge + updates + pub_maybe])
    state["last_run"] = dt.date.today().isoformat()
    state_mod.save_state(state)

    if not (keeps or updates or pub_maybe):
        print("Nothing to propose — no PR opened.")
        return

    readme = propose.README_PATH.read_text(encoding="utf-8")
    readme = propose.insert_rows(readme, [propose.make_row(c) for c in keeps])
    readme = propose.set_badge(readme, len(index) + len(keeps))  # keep the count badge current
    # Names repeat ("Yang et al." x3), so preprint-check updates carry their exact entry.
    by_name = {e.name: e for e in index}
    entry_for = {p.doi: p.entry for p in published}
    for c in updates:
        entry = entry_for.get(c.doi) or by_name.get(c.update_target)
        if entry:
            readme = propose.apply_update(readme, entry, c)
    propose.README_PATH.write_text(readme, encoding="utf-8")
    propose.regenerate_index()
    propose.regenerate_plot()

    branch = f"scout/{dt.date.today().isoformat()}"
    title = f"Paper Scout: {len(keeps)} additions, {len(updates)} updates"
    if pub_maybe:
        title += f", {len(pub_maybe)} to check"
    propose.open_pr(branch, title, body)
    print(f"Opened draft PR from branch {branch}.")


if __name__ == "__main__":
    main()
