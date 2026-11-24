#!/usr/bin/env python3
"""Build README rows from judged candidates and open a draft PR."""

from __future__ import annotations

import datetime as dt
import re
import subprocess

from config import PENDING_BRANCH, PROJECT_ROOT, README_PATH  # noqa: F401  (README_PATH is used via propose.README_PATH in run.py)
from dedup import Entry
from fetch import Candidate


def make_name(candidate: Candidate) -> str:
    """Derive the README display name.

    A title with a colon yields the part before it (e.g. "AlphaChimp: ..." ->
    "AlphaChimp"); otherwise fall back to "FirstAuthorSurname et al.".
    """
    if ":" in candidate.title:
        head = candidate.title.split(":", 1)[0].strip()
        if 0 < len(head) <= 40:
            return head
    if candidate.first_author:
        return f"{candidate.first_author.split()[-1]} et al."
    return candidate.title[:40]


def make_url(candidate: Candidate) -> str:
    """Return the canonical link for a candidate (DOI preferred, else arXiv)."""
    if candidate.doi:
        return f"https://doi.org/{candidate.doi}"
    if candidate.arxiv_id:
        return f"https://doi.org/10.48550/arXiv.{candidate.arxiv_id}"
    return candidate.landing_url


def make_row(candidate: Candidate) -> str:
    """Format a candidate as a README table row."""
    year = candidate.date[:4] or "????"
    tags = ", ".join(candidate.topic_tags) or "O"
    paper = f"[{make_name(candidate)}]({make_url(candidate)})"
    return (
        f"| {year} | {paper} | {tags} | {candidate.animal} | "
        f"{candidate.model_field} | {candidate.data_field} | {candidate.count_field} |"
    )


def _row_year(line: str) -> int | None:
    m = re.match(r"^\|\s*(\d{4})\s*\|", line)
    return int(m.group(1)) if m else None


def insert_row(readme_text: str, row: str) -> str:
    """Insert one row at the top of its year's block in the (newest-first) Projects table."""
    year = _row_year(row) or 9999
    lines = readme_text.splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == "### Projects")
        sep = next(i for i in range(start, len(lines)) if re.match(r"\|\s*-+", lines[i]))
    except StopIteration:  # fail loud rather than silently drop proposals
        raise ValueError("Could not locate the Projects table separator in README.md") from None
    pos = sep + 1
    while pos < len(lines) and lines[pos].startswith("|"):
        row_year = _row_year(lines[pos])
        if row_year is not None and row_year <= year:
            break
        pos += 1
    lines.insert(pos, row)
    return "\n".join(lines) + "\n"


def insert_rows(readme_text: str, rows: list[str]) -> str:
    """Insert each row at the top of its year's block (newest-first convention)."""
    for row in rows:
        readme_text = insert_row(readme_text, row)
    return readme_text


def apply_update(readme_text: str, entry: Entry, candidate: Candidate) -> str:
    """Swap a listed entry's link to the published version, bump its year, and re-place the row."""
    old_paper_cell = entry.cells[1]
    new_year = candidate.date[:4] or entry.year
    new_paper_cell = f"[{entry.name}]({make_url(candidate)})"
    new_cells = list(entry.cells)
    new_cells[0] = new_year
    new_cells[1] = new_paper_cell
    new_line = "| " + " | ".join(new_cells) + " |"

    lines = readme_text.splitlines()
    hits = [i for i, l in enumerate(lines) if old_paper_cell in l and l.lstrip().startswith("|")]
    if not hits:
        return readme_text  # entry not found; leave the README untouched
    if "### Projects" not in readme_text:  # bare table fragment: update in place
        for i in hits:
            lines[i] = new_line
        return "\n".join(lines) + "\n"
    kept = [l for i, l in enumerate(lines) if i not in hits]
    return insert_row("\n".join(kept) + "\n", new_line)


def build_pr_body(keeps, reviews, updates, rejects, maybe_updates=()) -> str:
    """Assemble the markdown PR body from the four candidate buckets."""
    today = dt.date.today().isoformat()
    parts = [f"🐒 **Paper Scout** — week of {today}", ""]

    if keeps:
        parts += ["### ✅ Proposed additions", "",
                  "| Year | Paper | Topic | Animal | Model? | Data? | Count | Score | Why |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for c in keeps:
            parts.append(f"{make_row(c)} {c.score:.2f} | {c.reason} |")
        parts.append("")
    if updates:
        parts += ["### 🔁 Published versions of existing entries", ""]
        for c in updates:
            why = f" — _{c.reason}_" if c.reason else ""
            parts.append(f"- **{c.update_target}** → {make_url(c)} (bump year to {c.date[:4]}){why}")
        parts.append("")
    if maybe_updates:
        parts += ["### 🔎 Possible published versions — NOT applied, check by hand", ""]
        for c in maybe_updates:
            parts.append(f"- **{c.update_target}** → {make_url(c)} ({c.date[:4]}) — _{c.reason}_")
        parts.append("")
    if reviews:
        parts += ["### 🔍 Borderline — needs your call", ""]
        for c in reviews:
            parts.append(f"- {make_name(c)} ({c.date[:4]}) — score {c.score:.2f}: _{c.reason}_  {make_url(c)}")
        parts.append("")
    if rejects:
        parts += ["<details><summary>🗑 Rejected (audit)</summary>", ""]
        for c in rejects:
            parts.append(f"- {make_name(c)} — _{c.reason}_")
        parts += ["", "</details>"]
    return "\n".join(parts)


PENDING_TITLE = "Paper Scout: pending proposals"
MAX_BODY_CHARS = 60_000  # GitHub caps PR bodies at 65,536


def _git(*args: str, capture: bool = False) -> str:
    res = subprocess.run(args, check=True, cwd=PROJECT_ROOT, capture_output=capture, text=True)
    return res.stdout.strip() if capture else ""


def checkout_pending() -> int | None:
    """Switch to the rolling scout PR's branch if one is open; return its PR number.

    Weekly proposals accumulate on one draft PR instead of one PR per week, so they
    never conflict with each other. Call this before editing README.md. With no
    open pending PR, a fresh branch is started from the current checkout (main).
    """
    number = _git("gh", "pr", "list", "--head", PENDING_BRANCH, "--state", "open",
                  "--json", "number", "--jq", ".[0].number // empty", capture=True)
    if number:
        _git("git", "fetch", "--depth=1", "origin", PENDING_BRANCH)
        _git("git", "checkout", "-B", PENDING_BRANCH, "FETCH_HEAD")
        return int(number)
    _git("git", "checkout", "-B", PENDING_BRANCH)
    return None


def publish(pr_number: int | None, title: str, body: str) -> None:
    """Commit README.md to the pending branch and open or update the draft PR.

    Only README.md is committed: the site, badge and growth figure are built from
    it at deploy time, so proposals never collide on derived files.
    """
    _git("git", "add", "README.md")
    _git("git", "commit", "-m", title)
    if pr_number is None:
        # A merged or closed pending PR can leave a stale branch behind; replace it.
        _git("git", "push", "--force", "-u", "origin", PENDING_BRANCH)
        _git("gh", "pr", "create", "--draft", "--head", PENDING_BRANCH,
             "--title", PENDING_TITLE, "--body", body[:MAX_BODY_CHARS])
        return
    _git("git", "push", "origin", PENDING_BRANCH)
    old = _git("gh", "pr", "view", str(pr_number), "--json", "body", "--jq", ".body", capture=True)
    merged = (body + "\n\n---\n\n" + old)[:MAX_BODY_CHARS]
    _git("gh", "pr", "edit", str(pr_number), "--body", merged)
