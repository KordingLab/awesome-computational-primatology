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


def _is_separator(line: str) -> bool:
    return bool(re.match(r"^\|(\s*:?-+:?\s*\|)+\s*$", line.strip()))


def _insert_in_table(lines: list[str], sep: int, row: str) -> None:
    """Insert row (in place) at the top of its year's block in the table whose separator is at sep."""
    year = _row_year(row) or 9999
    pos = sep + 1
    while pos < len(lines) and lines[pos].startswith("|"):
        row_year = _row_year(lines[pos])
        if row_year is not None and row_year <= year:
            break
        pos += 1
    lines.insert(pos, row)


def insert_row(readme_text: str, row: str) -> str:
    """Insert one row at the top of its year's block in the (newest-first) Projects table."""
    lines = readme_text.splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == "### Projects")
        sep = next(i for i in range(start, len(lines)) if _is_separator(lines[i]))
    except StopIteration:  # fail loud rather than silently drop proposals
        raise ValueError("Could not locate the Projects table separator in README.md") from None
    _insert_in_table(lines, sep, row)
    return "\n".join(lines) + "\n"


def insert_rows(readme_text: str, rows: list[str]) -> str:
    """Insert each row at the top of its year's block (newest-first convention)."""
    for row in rows:
        readme_text = insert_row(readme_text, row)
    return readme_text


def apply_update(readme_text: str, entry: Entry, candidate: Candidate) -> str:
    """Swap a listed entry's link to the published version and bump its year.

    The row stays in the table it came from (e.g. the cross-species dataset table);
    if the year changes it moves to the top of its new year's block there.
    """
    old_paper_cell = entry.cells[1]
    new_year = candidate.date[:4] or entry.year
    new_cells = list(entry.cells)
    new_cells[0] = new_year
    new_cells[1] = f"[{entry.name}]({make_url(candidate)})"
    new_line = "| " + " | ".join(new_cells) + " |"

    lines = readme_text.splitlines()
    hit = next((i for i, l in enumerate(lines)
                if old_paper_cell in l and l.lstrip().startswith("|")), None)
    if hit is None:
        return readme_text  # entry not found; leave the README untouched
    sep = next((i for i in range(hit - 1, -1, -1) if _is_separator(lines[i])), None)
    if sep is None or _row_year(lines[hit]) == _row_year(new_line):
        lines[hit] = new_line  # same year (or no table found): update in place
    else:
        del lines[hit]
        _insert_in_table(lines, sep, new_line)
    return "\n".join(lines) + "\n"


def _table_rows(text: str) -> list[str]:
    return [l for l in text.splitlines() if _row_year(l) is not None]


def _row_name(line: str) -> str:
    cells = line.split("|")
    m = re.search(r"\[([^\]]*)\]", cells[2]) if len(cells) > 2 else None
    return m.group(1) if m else ""


def carry_over(main_text: str, base_text: str, pending_text: str) -> str:
    """Row-level three-way merge: replay the pending branch's table edits onto main.

    Rows the pending branch added (relative to its merge base with main) are inserted
    into main's README; rows it replaced (published-version updates) are swapped in
    the table they live in. Rows main already has, or main changed independently, are
    left as main has them. This keeps the rolling scout PR conflict-free however main
    moved in the meantime.
    """
    base, pending = set(_table_rows(base_text)), set(_table_rows(pending_text))
    added = [l for l in _table_rows(pending_text) if l not in base]
    replaced = {_row_name(l): l for l in base - pending}
    lines = main_text.splitlines()
    present = set(lines)

    for row in reversed(added):  # reversed + insert-at-top keeps their original order
        if row in present:
            continue
        old = replaced.get(_row_name(row))
        if old is not None and old in present:  # an update: keep it in its own table
            hit = lines.index(old)
            sep = next((i for i in range(hit - 1, -1, -1) if _is_separator(lines[i])), None)
            if sep is None or _row_year(old) == _row_year(row):
                lines[hit] = row
            else:
                del lines[hit]
                _insert_in_table(lines, sep, row)
        else:
            lines = insert_row("\n".join(lines) + "\n", row).splitlines()
        present = set(lines)
    return "\n".join(lines) + "\n"


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


def _git(*args: str, capture: bool = False, check: bool = True) -> str:
    res = subprocess.run(args, check=check, cwd=PROJECT_ROOT, capture_output=capture, text=True)
    return res.stdout.strip() if capture else ""


def prepare_pending() -> tuple[int | None, str]:
    """Check out scout/pending rebuilt on current main; return (open PR number, old tip).

    Weekly proposals accumulate on one draft PR. Each run rebuilds that branch from
    main and replays its table rows with carry_over(), so it never goes stale or
    conflicts with human PRs, and the dedup index (built afterwards from the
    working-tree README) already contains every pending row.
    Requires a full clone (checkout fetch-depth: 0) for the merge base.
    """
    _git("git", "fetch", "origin", "main")
    number = _git("gh", "pr", "list", "--head", PENDING_BRANCH, "--state", "open",
                  "--json", "number", "--jq", ".[0].number // empty", capture=True)
    _git("git", "checkout", "-B", PENDING_BRANCH, "origin/main")
    if not number:
        return None, ""
    _git("git", "fetch", "origin", PENDING_BRANCH)
    tip = _git("git", "rev-parse", "FETCH_HEAD", capture=True)
    base = _git("git", "merge-base", "origin/main", tip, capture=True)
    show = lambda rev: _git("git", "show", f"{rev}:README.md", capture=True) + "\n"  # noqa: E731
    merged = carry_over(README_PATH.read_text(encoding="utf-8"), show(base), show(tip))
    README_PATH.write_text(merged, encoding="utf-8")
    _git("git", "add", "README.md")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=PROJECT_ROOT).returncode:
        _git("git", "commit", "-m", "Paper Scout: carry over pending proposals onto main")
    return int(number), tip


def publish(pr_number: int | None, old_tip: str, title: str, body: str) -> None:
    """Commit README.md to scout/pending, push, and open or update the draft PR.

    Only README.md is committed: the site, badge and growth figure are built from
    it at deploy time. A run that changes nothing (e.g. only "possible published
    versions" to check by hand) still records its report on an open PR.
    """
    _git("git", "add", "README.md")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=PROJECT_ROOT).returncode:
        _git("git", "commit", "-m", title)
    has_rows = _git("git", "rev-list", "--count", "origin/main..HEAD", capture=True) != "0"

    if pr_number is None:
        if not has_rows:
            print("No README changes to propose; no PR opened. Report:\n\n" + body)
            return
        # A merged or closed pending PR can leave a stale branch behind; replace it.
        _git("git", "push", "--force", "-u", "origin", PENDING_BRANCH)
        _git("gh", "pr", "create", "--draft", "--head", PENDING_BRANCH,
             "--title", PENDING_TITLE, "--body", body[:MAX_BODY_CHARS])
        return
    # The branch was rebuilt on main, so the push rewrites it; the lease refuses if
    # someone pushed to it since we fetched.
    _git("git", "push", f"--force-with-lease={PENDING_BRANCH}:{old_tip}", "origin", PENDING_BRANCH)
    old = _git("gh", "pr", "view", str(pr_number), "--json", "body", "--jq", ".body", capture=True)
    merged = (body + "\n\n---\n\n" + old)[:MAX_BODY_CHARS]
    _git("gh", "pr", "edit", str(pr_number), "--body", merged)
