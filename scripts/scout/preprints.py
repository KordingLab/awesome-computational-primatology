#!/usr/bin/env python3
"""Find published versions of preprints already listed in the README.

Every listed arXiv / bioRxiv / eLife-reviewed-preprint entry is checked on each run,
so a paper that was listed as a preprint is moved to its journal / proceedings
version once one exists. Evidence, strongest first:

  1. registry links — bioRxiv's publication API, Crossref ``is-preprint-of``,
     the arXiv record's own DOI field, and Semantic Scholar's merged record;
  2. eLife versioning — a reviewed preprint ``10.7554/elife.N.V`` whose Version of
     Record ``10.7554/elife.N`` now exists;
  3. an OpenAlex search of the preprint's first author's later works, accepted only
     when the author lists overlap strongly AND the titles agree. This catches
     papers whose title changed on publication (MacAction → "Realistic monkey body
     animation reveals an uncanny valley…", which no registry linked).

Each hit is verified against Crossref (exists, is not itself a preprint) before
it is proposed. Matches from (1)–(2), or (3) with near-identical titles, are
"high" confidence and are applied to the README; weaker author-search matches
are "low" and only listed in the PR body for a human to check.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
from dataclasses import dataclass
from difflib import SequenceMatcher

from config import MAILTO
from dedup import Entry
from fetch import _get

# DOI prefixes / patterns that denote preprints (not a final published version).
PREPRINT_DOI = re.compile(
    r"^10\.(48550/arxiv\.|1101/|64898/|21203/rs\.|20944/preprints|31219/osf\.io|2139/ssrn\.|36227/techrxiv\.)"
    r"|^10\.7554/elife\.\d+\.\d+$"
)
# Crossref work types that are a final, citable version.
PUBLISHED_TYPES = {"journal-article", "proceedings-article", "book-chapter"}

NET_ERRORS = (urllib.error.URLError, TimeoutError, ConnectionError, ValueError, KeyError)


@dataclass
class PublishedVersion:
    """A published version found for a listed preprint entry."""

    entry: Entry
    doi: str            # normalized, lowercase
    title: str
    venue: str
    date: str           # YYYY-MM-DD (or YYYY-MM / YYYY)
    evidence: str       # which source linked them
    confidence: str     # "high" | "low"


def is_preprint_doi(doi: str) -> bool:
    """True if a (normalized) DOI belongs to a preprint server or eLife RP version."""
    return bool(PREPRINT_DOI.search(doi.lower()))


def _json(url: str) -> dict:
    return json.loads(_get(url, timeout=30))


def _norm_title(t: str) -> str:
    t = re.sub(r"<[^>]+>", " ", t or "")
    return " ".join(re.findall(r"[a-z0-9]+", t.lower()))


def title_similarity(a: str, b: str) -> float:
    """Ratio in [0, 1] between two titles after normalization."""
    return SequenceMatcher(None, _norm_title(a), _norm_title(b)).ratio()


def _surname(name: str) -> str:
    parts = re.findall(r"[a-zà-ÿ'-]+", (name or "").lower())
    return parts[-1] if parts else ""


def author_overlap(a: list[str], b: list[str]) -> float:
    """Fraction of the shorter author list whose surnames appear in the other."""
    sa, sb = {_surname(x) for x in a if x}, {_surname(x) for x in b if x}
    sa.discard(""); sb.discard("")
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / min(len(sa), len(sb))


# ---- metadata -------------------------------------------------------------

def crossref_work(doi: str) -> dict | None:
    """Crossref record for a DOI, or None if unregistered / unreachable."""
    try:
        return _json(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}?mailto={MAILTO}")["message"]
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    except NET_ERRORS:
        return None


def _crossref_date(msg: dict) -> str:
    for key in ("published-print", "published-online", "published", "issued"):
        parts = ((msg.get(key) or {}).get("date-parts") or [[None]])[0]
        if parts and parts[0]:
            return "-".join(f"{p:02d}" if i else str(p) for i, p in enumerate(parts))
    return ""


def preprint_metadata(entry: Entry) -> dict | None:
    """Title, authors and date of a listed preprint, from OpenAlex."""
    doi = entry.doi or (f"10.48550/arxiv.{entry.arxiv_id}" if entry.arxiv_id else "")
    if not doi:
        return None
    try:
        w = _json(f"https://api.openalex.org/works/doi:{doi}?mailto={MAILTO}")
    except (urllib.error.HTTPError, *NET_ERRORS):
        return None
    return {
        "doi": doi.lower(),
        "title": w.get("title") or "",
        "date": w.get("publication_date") or "",
        "authors": [(a.get("author") or {}).get("display_name", "") for a in w.get("authorships") or []],
        "first_author_id": ((w.get("authorships") or [{}])[0].get("author") or {}).get("id", ""),
    }


# ---- evidence sources -----------------------------------------------------

def from_biorxiv(doi: str) -> list[tuple[str, str]]:
    """bioRxiv's own preprint → publication link."""
    if not re.match(r"^10\.(1101|64898)/", doi):
        return []
    try:
        coll = _json(f"https://api.biorxiv.org/pubs/biorxiv/{doi}").get("collection") or []
    except (urllib.error.HTTPError, *NET_ERRORS):
        return []
    return [(c["published_doi"].lower(), "bioRxiv publication link") for c in coll if c.get("published_doi")]


def from_crossref_relation(doi: str) -> list[tuple[str, str]]:
    """Crossref ``is-preprint-of`` relation registered by the preprint server."""
    msg = crossref_work(doi) or {}
    rel = (msg.get("relation") or {}).get("is-preprint-of") or []
    return [(r["id"].lower(), "Crossref is-preprint-of") for r in rel if r.get("id-type") == "doi"]


def from_arxiv(arxiv_id: str) -> list[tuple[str, str]]:
    """DOI the authors attached to their arXiv record."""
    if not arxiv_id:
        return []
    try:
        raw = _get(f"https://export.arxiv.org/api/query?id_list={arxiv_id}", timeout=60, attempts=3, backoff=5)
    except (urllib.error.HTTPError, *NET_ERRORS):
        return []
    m = re.search(rb"<arxiv:doi[^>]*>([^<]+)</arxiv:doi>", raw)
    return [(m.group(1).decode().strip().lower(), "arXiv record DOI")] if m else []


def from_semantic_scholar(entry: Entry) -> list[tuple[str, str]]:
    """Semantic Scholar merges preprint and published records; take its non-preprint DOI."""
    key = f"arXiv:{entry.arxiv_id}" if entry.arxiv_id else f"DOI:{entry.doi}"
    try:
        p = _json(f"https://api.semanticscholar.org/graph/v1/paper/{key}?fields=externalIds")
    except (urllib.error.HTTPError, *NET_ERRORS):
        return []
    doi = ((p.get("externalIds") or {}).get("DOI") or "").lower()
    return [(doi, "Semantic Scholar merged record")] if doi else []


def from_elife_vor(doi: str) -> list[tuple[str, str]]:
    """Version of Record of an eLife reviewed preprint (10.7554/elife.N.V → 10.7554/elife.N)."""
    m = re.match(r"^(10\.7554/elife\.\d+)\.\d+$", doi)
    if not m:
        return []
    msg = crossref_work(m.group(1))
    return [(m.group(1), "eLife Version of Record")] if msg else []


def from_author_search(meta: dict) -> list[tuple[str, str, str]]:
    """Later non-preprint works by the preprint's first author with a matching author list.

    Returns (doi, evidence, confidence) — "high" only for near-identical titles.
    """
    if not meta.get("first_author_id") or not meta.get("date"):
        return []
    author = meta["first_author_id"].rsplit("/", 1)[-1]
    params = urllib.parse.urlencode({
        "filter": f"author.id:{author},from_publication_date:{meta['date']},"
                  "type:article|book-chapter",
        "per-page": "50", "mailto": MAILTO,
    })
    try:
        results = _json(f"https://api.openalex.org/works?{params}").get("results") or []
    except (urllib.error.HTTPError, *NET_ERRORS):
        return []
    out = []
    for w in results:
        doi = (w.get("doi") or "").replace("https://doi.org/", "").lower()
        if not doi or doi == meta["doi"] or is_preprint_doi(doi):
            continue
        authors = [(a.get("author") or {}).get("display_name", "") for a in w.get("authorships") or []]
        overlap = author_overlap(meta["authors"], authors)
        sim = title_similarity(meta["title"], w.get("title") or "")
        if overlap >= 0.8 and sim >= 0.9:
            out.append((doi, f"same authors, title match {sim:.2f}", "high"))
        elif overlap >= 0.6 and sim >= 0.45:
            out.append((doi, f"author overlap {overlap:.0%}, title similarity {sim:.2f}", "low"))
    return out


# ---- driver ---------------------------------------------------------------

def find_published(entry: Entry, pause: float = 1.0) -> PublishedVersion | None:
    """Return the best verified published version of a listed preprint, if any."""
    doi = entry.doi or (f"10.48550/arxiv.{entry.arxiv_id}" if entry.arxiv_id else "")
    if not doi or not is_preprint_doi(doi):
        return None

    linked: list[tuple[str, str, str]] = []
    for source in (from_elife_vor, from_biorxiv, from_crossref_relation):
        linked += [(d, ev, "high") for d, ev in source(doi)]
    linked += [(d, ev, "high") for d, ev in from_arxiv(entry.arxiv_id)]
    linked += [(d, ev, "high") for d, ev in from_semantic_scholar(entry)]
    time.sleep(pause)  # Semantic Scholar's keyless pool allows ~1 request/s

    meta = None
    if not any(not is_preprint_doi(d) for d, _, _ in linked):
        meta = preprint_metadata(entry)
        if meta:
            linked += from_author_search(meta)

    linked.sort(key=lambda x: x[2] != "high")  # registry links first, stable otherwise
    for cand_doi, evidence, confidence in linked:
        if not cand_doi or cand_doi == doi or is_preprint_doi(cand_doi):
            continue
        msg = crossref_work(cand_doi)
        # posted-content, peer-review, dataset, component… are not published versions.
        if not msg or msg.get("type") not in PUBLISHED_TYPES:
            continue
        title = (msg.get("title") or [""])[0]
        if confidence == "high" and evidence.startswith(("Semantic", "arXiv")):
            # These sources occasionally attach a different paper's DOI; require the
            # titles to be recognisably the same work before trusting them blindly.
            meta = meta or preprint_metadata(entry)
            if meta and title_similarity(meta["title"], title) < 0.6:
                confidence = "low"
        return PublishedVersion(
            entry=entry, doi=cand_doi, title=re.sub(r"<[^>]+>", "", title),
            venue=(msg.get("container-title") or [""])[0] or msg.get("publisher", ""),
            date=_crossref_date(msg), evidence=evidence, confidence=confidence,
        )
    return None


def find_all(index: list[Entry], skip_dois: set[str] = frozenset()) -> list[PublishedVersion]:
    """Check every listed preprint; skip published DOIs already proposed in earlier runs."""
    found = []
    for entry in index:
        try:
            hit = find_published(entry)
        except Exception as exc:  # noqa: BLE001 - one bad lookup must not sink the run
            print(f"  preprint check failed for {entry.name}: {exc!r}")
            continue
        if hit and f"doi:{hit.doi}" not in skip_dois:
            found.append(hit)
    return found


if __name__ == "__main__":  # manual audit: python scripts/scout/preprints.py
    import dedup

    idx = dedup.load_index()
    pre = [e for e in idx if is_preprint_doi(e.doi or (f"10.48550/arxiv.{e.arxiv_id}" if e.arxiv_id else ""))]
    print(f"Checking {len(pre)} preprint entries…")
    for hit in find_all(pre):
        print(f"[{hit.confidence}] {hit.entry.year} {hit.entry.name}: {hit.entry.doi or hit.entry.arxiv_id}"
              f"\n    → {hit.doi} ({hit.date[:4]}, {hit.venue}) — {hit.evidence}\n      {hit.title[:110]}")
