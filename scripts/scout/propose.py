#!/usr/bin/env python3
"""Build README rows from judged candidates and open a draft PR."""

from __future__ import annotations

import datetime as dt
import re
import subprocess

from config import PROJECT_ROOT, README_PATH, WEBSITE_GENERATOR
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


def insert_rows(readme_text: str, rows: list[str]) -> str:
    """Insert new rows at the top of the Projects table (newest-first convention)."""
    if not rows:
        return readme_text
    lines = readme_text.splitlines()
    out: list[str] = []
    inserted = False
    in_projects = False
    seen_separator = False
    for line in lines:
        out.append(line)
        if line.strip() == "### Projects":
            in_projects = True
        elif in_projects and not seen_separator and re.match(r"\|\s*-+", line):
            seen_separator = True
            out.extend(rows)
            inserted = True
    if not inserted:  # fail loud rather than silently drop proposals
        raise ValueError("Could not locate the Projects table separator in README.md")
    return "\n".join(out) + "\n"


def apply_update(readme_text: str, entry: Entry, candidate: Candidate) -> str:
    """Swap a listed entry's link to the published version and bump its year."""
    old_paper_cell = entry.cells[1]
    new_year = candidate.date[:4] or entry.year
    new_paper_cell = f"[{entry.name}]({make_url(candidate)})"
    new_cells = list(entry.cells)
    new_cells[0] = new_year
    new_cells[1] = new_paper_cell
    new_line = "| " + " | ".join(new_cells) + " |"

    out = []
    for line in readme_text.splitlines():
        if old_paper_cell in line and line.lstrip().startswith("|"):
            out.append(new_line)
        else:
            out.append(line)
    return "\n".join(out) + "\n"


def regenerate_index() -> None:
    """Regenerate index.html so website.yml's sync check passes."""
    subprocess.run(["python", str(WEBSITE_GENERATOR)], check=True, cwd=PROJECT_ROOT)


def build_pr_body(keeps, reviews, updates, rejects) -> str:
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
            parts.append(f"- **{c.update_target}** → {make_url(c)} (bump year to {c.date[:4]})")
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


def open_pr(branch: str, title: str, body: str) -> None:
    """Commit the working tree to a new branch and open a draft PR via gh."""
    run = lambda *a: subprocess.run(a, check=True, cwd=PROJECT_ROOT)
    run("git", "checkout", "-b", branch)
    run("git", "add", "README.md", "index.html", "docs/scout-state.json")
    run("git", "commit", "-m", title)
    run("git", "push", "-u", "origin", branch)
    run("gh", "pr", "create", "--draft", "--title", title, "--body", body)
