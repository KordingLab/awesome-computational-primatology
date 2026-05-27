#!/usr/bin/env python3
"""Deduplicate / version-match candidates against the existing README list.

Three-way classification:
  * SKIP   — exact DOI or arXiv id already listed.
  * UPDATE — a listed "tool" entry (e.g. AlphaChimp, PriMAT) whose name appears in
             the candidate title; almost certainly the published version of a
             listed preprint. Proposed as a link/year update, not a new row.
  * NEW    — everything else.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from config import README_PATH
from fetch import Candidate


@dataclass
class Entry:
    """A parsed README row."""

    name: str
    year: str
    doi: str
    arxiv_id: str
    tool_token: str  # normalized distinctive name, or "" for author-style entries
    cells: list[str]


def _words(text: str) -> list[str]:
    """Lowercase word tokens of length >= 2 ([a-z0-9]+)."""
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) >= 2]


def _tool_token(name: str) -> str:
    """Derive a distinctive tool name (space-joined words) from a README entry.

    Returns "" for author-style names ("Mueller et al.", "Loos & Ernst") and for
    tokens too short/generic to match safely (e.g. single words < 5 chars).
    """
    base = name.split("(")[0].strip()  # drop trailing "(Vogg et al.)"
    if "et al" in base.lower():
        return ""
    parts = base.split()
    looks_human = (
        len(parts) <= 3
        and not any(ch.isdigit() for ch in base)
        and all(re.fullmatch(r"[A-Z][a-zé'’.-]+", w) or w == "&" for w in parts)
    )
    if looks_human:
        return ""
    words = _words(base)
    if not words:
        return ""
    if len(words) == 1 and len(words[0]) < 5:  # avoid trivial single tokens (e.g. "tri")
        return ""
    return " ".join(words)


def _contains_phrase(title: str, phrase: str) -> bool:
    """True if the phrase's words appear as a contiguous run of whole title words."""
    hay = _words(title)
    needle = phrase.split()
    return any(hay[i:i + len(needle)] == needle for i in range(len(hay) - len(needle) + 1))


def _id_from_url(url: str) -> tuple[str, str]:
    """Extract (doi, arxiv_id) from a paper link URL."""
    doi = ""
    arxiv_id = ""
    m = re.search(r"doi\.org/(10\.[^\s)]+)", url)
    if m:
        doi = m.group(1).lower().rstrip(".")
    m = re.search(r"arxiv\.(?:org|2\d{3})[/.](?:abs/)?(\d{4}\.\d{4,5})", url)
    if m:
        arxiv_id = m.group(1)
    m = re.search(r"10\.48550/arxiv\.(\d{4}\.\d{4,5})", url, re.IGNORECASE)
    if m:
        arxiv_id = m.group(1)
    return doi, arxiv_id


def load_index(readme_path=README_PATH) -> list[Entry]:
    """Parse README.md into a list of Entry records (7-column rows only)."""
    text = readme_path.read_text(encoding="utf-8")
    entries: list[Entry] = []
    in_projects = False
    for line in text.splitlines():
        if line.strip() == "### Projects":
            in_projects = True
            continue
        if not in_projects or line.count("|") != 8:
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if cells[0] == "Year" or all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue
        m = re.match(r"\[(.*?)\]\((.*?)\)", cells[1])
        name = m.group(1) if m else cells[1]
        url = m.group(2) if m else ""
        doi, arxiv_id = _id_from_url(url)
        entries.append(
            Entry(name=name, year=cells[0], doi=doi, arxiv_id=arxiv_id,
                  tool_token=_tool_token(name), cells=cells)
        )
    return entries


def classify(candidate: Candidate, index: list[Entry]) -> Candidate:
    """Set candidate.classification (SKIP/UPDATE/NEW) in place and return it."""
    known_dois = {e.doi for e in index if e.doi}
    known_arxiv = {e.arxiv_id for e in index if e.arxiv_id}

    if (candidate.doi and candidate.doi in known_dois) or (
        candidate.arxiv_id and candidate.arxiv_id in known_arxiv
    ):
        candidate.classification = "SKIP"
        return candidate

    for e in index:
        if e.tool_token and _contains_phrase(candidate.title, e.tool_token):
            candidate.classification = "UPDATE"
            candidate.update_target = e.name
            candidate.match_confidence = "high"
            return candidate

    candidate.classification = "NEW"
    return candidate


def classify_all(candidates: list[Candidate], index: list[Entry]) -> list[Candidate]:
    """Classify every candidate against the index."""
    return [classify(c, index) for c in candidates]
