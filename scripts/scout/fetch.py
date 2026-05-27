#!/usr/bin/env python3
"""Fetch recent candidate papers from OpenAlex and arXiv (date-windowed)."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from config import (
    ARXIV_CATEGORIES,
    ANIMAL_TERMS,
    MAILTO,
    METHOD_TERMS,
    OPENALEX_SEARCHES,
)

USER_AGENT = f"awesome-computational-primatology-scout (mailto:{MAILTO})"


@dataclass
class Candidate:
    """A fetched paper plus the fields each pipeline stage fills in."""

    source: str          # "openalex" | "arxiv"
    title: str
    abstract: str
    doi: str             # normalized: lowercase, no scheme; "" if none
    arxiv_id: str        # e.g. "2410.17136"; "" if none
    date: str            # YYYY-MM-DD
    venue: str
    authors: list[str]
    landing_url: str = ""
    pdf_url: str = ""

    # DEDUP
    classification: str = "NEW"   # SKIP | UPDATE | NEW
    update_target: str = ""       # README entry name this would update
    match_confidence: str = ""    # "high" | "low" (for UPDATE)

    # PREFILTER
    prefilter_score: float = 0.0
    is_tangent: bool = False

    # JUDGE
    decision: str = ""            # KEEP | REVIEW | REJECT
    score: float = 0.0
    reason: str = ""
    animal: str = ""
    topic_tags: list[str] = field(default_factory=list)

    # ENRICH
    model_field: str = "N/A"
    data_field: str = "N/A"
    count_field: str = "N/A"

    @property
    def first_author(self) -> str:
        """Return the first author's full name, or '' if unknown."""
        return self.authors[0] if self.authors else ""

    @property
    def text(self) -> str:
        """Return title + abstract for filtering/ranking."""
        return f"{self.title} {self.abstract}".strip()

    @property
    def work_key(self) -> str:
        """Stable identity for state/dedup: arXiv id, else DOI, else norm title."""
        if self.arxiv_id:
            return f"arxiv:{self.arxiv_id}"
        if self.doi:
            return f"doi:{self.doi}"
        return "title:" + re.sub(r"[^a-z0-9]+", "", self.title.lower())


def _norm_doi(doi: str | None) -> str:
    """Normalize a DOI to lowercase bare form (no scheme)."""
    if not doi:
        return ""
    return doi.replace("https://doi.org/", "").replace("http://doi.org/", "").lower().strip()


def _reconstruct_abstract(inverted: dict | None) -> str:
    """Rebuild plain text from an OpenAlex abstract_inverted_index."""
    if not inverted:
        return ""
    positions = [(i, word) for word, idxs in inverted.items() for i in idxs]
    return " ".join(w for _, w in sorted(positions))


def _get(url: str, timeout: int = 30) -> bytes:
    """HTTP GET with a polite User-Agent."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_openalex(since: str) -> list[Candidate]:
    """Fetch candidates from OpenAlex, unioned over the configured searches.

    Args:
        since: ISO date (YYYY-MM-DD); only works published on/after are returned.

    Returns:
        Deduplicated (by OpenAlex id) list of candidates.
    """
    seen: dict[str, Candidate] = {}
    for query in OPENALEX_SEARCHES:
        params = urllib.parse.urlencode(
            {
                "search": query,
                "filter": f"from_publication_date:{since}",
                "sort": "publication_date:desc",
                "per-page": "50",
                "mailto": MAILTO,
            }
        )
        results = json.loads(_get(f"https://api.openalex.org/works?{params}"))["results"]
        for w in results:
            wid = w["id"]
            if wid in seen:
                continue
            primary = w.get("primary_location") or {}
            authors = [
                (a.get("author") or {}).get("display_name", "")
                for a in (w.get("authorships") or [])
            ]
            seen[wid] = Candidate(
                source="openalex",
                title=w.get("title") or "",
                abstract=_reconstruct_abstract(w.get("abstract_inverted_index")),
                doi=_norm_doi(w.get("doi")),
                arxiv_id="",
                date=w.get("publication_date") or "",
                venue=(primary.get("source") or {}).get("display_name") or "",
                authors=[a for a in authors if a],
                landing_url=primary.get("landing_page_url") or "",
                pdf_url=(w.get("best_oa_location") or {}).get("pdf_url") or "",
            )
        time.sleep(0.3)  # polite to the keyless pool
    return list(seen.values())


def _arxiv_query() -> str:
    """Build the arXiv search_query string (categories AND primate/method terms)."""
    cats = " OR ".join(f"cat:{c}" for c in ARXIV_CATEGORIES)
    animals = " OR ".join(f'all:{t}' for t in ANIMAL_TERMS[:10])
    methods = " OR ".join(f'all:"{t}"' for t in ["pose", "behavior", "detection",
                                                  "face recognition", "tracking",
                                                  "vocalization"])
    return f"({cats}) AND ({animals}) AND ({methods})"


def fetch_arxiv(since: str, max_results: int = 100) -> list[Candidate]:
    """Fetch recent arXiv preprints matching the scout's scope.

    Args:
        since: ISO date (YYYY-MM-DD); entries published before are dropped.
        max_results: Cap on results requested from the arXiv API.

    Returns:
        List of candidates from arXiv.
    """
    params = urllib.parse.urlencode(
        {
            "search_query": _arxiv_query(),
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": str(max_results),
        }
    )
    raw = _get(f"http://export.arxiv.org/api/query?{params}")
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    out: list[Candidate] = []
    for entry in ET.fromstring(raw).findall("atom:entry", ns):
        published = (entry.findtext("atom:published", default="", namespaces=ns))[:10]
        if published < since:
            continue
        abs_url = entry.findtext("atom:id", default="", namespaces=ns)
        arxiv_id = re.sub(r"v\d+$", "", abs_url.rsplit("/", 1)[-1]) if abs_url else ""
        doi_el = entry.find("arxiv:doi", ns)
        out.append(
            Candidate(
                source="arxiv",
                title=" ".join((entry.findtext("atom:title", default="", namespaces=ns)).split()),
                abstract=" ".join((entry.findtext("atom:summary", default="", namespaces=ns)).split()),
                doi=_norm_doi(doi_el.text if doi_el is not None else ""),
                arxiv_id=arxiv_id,
                date=published,
                venue="arXiv",
                authors=[a.findtext("atom:name", default="", namespaces=ns)
                         for a in entry.findall("atom:author", ns)],
                landing_url=abs_url,
                pdf_url=abs_url.replace("/abs/", "/pdf/") if abs_url else "",
            )
        )
    return out


def _dedup_by_title(candidates: list[Candidate]) -> list[Candidate]:
    """Collapse the same paper fetched from multiple sources, preferring a DOI."""
    best: dict[str, Candidate] = {}
    for c in candidates:
        key = re.sub(r"[^a-z0-9]+", "", c.title.lower())[:60]
        if not key:
            best[c.work_key] = c
        elif key not in best or (not best[key].doi and c.doi):
            best[key] = c
    return list(best.values())


def fetch_all(since: str) -> list[Candidate]:
    """Fetch from every source; arXiv failures degrade gracefully (skip source).

    Args:
        since: ISO date (YYYY-MM-DD).

    Returns:
        Combined, cross-source-deduplicated candidate list.
    """
    candidates = fetch_openalex(since)
    try:
        candidates += fetch_arxiv(since)
    except (urllib.error.URLError, ET.ParseError) as exc:
        print(f"  arXiv fetch failed ({exc}); continuing with OpenAlex only.")
    return _dedup_by_title(candidates)
