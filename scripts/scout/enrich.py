#!/usr/bin/env python3
"""Fill the Model? / Data? / Image-Video-Count columns. Honest negative is N/A, not TBD."""

from __future__ import annotations

import re
import urllib.error
import urllib.request

from config import CODE_HOSTS, DATA_HOSTS, MAILTO
from fetch import Candidate

_COUNT_RE = re.compile(
    r"([\d][\d,]*)\s*([kKmM])?\+?\s*"
    r"(images?|frames?|videos?|clips?|photos?|sequences?|annotations?|"
    r"bounding boxes|bboxes|labels?)",
)
_UA = {"User-Agent": f"awesome-computational-primatology-scout (mailto:{MAILTO})"}


def _numeric(value: str, unit: str | None) -> float:
    """Convert '3,385' + 'k' to a comparable float."""
    n = float(value.replace(",", ""))
    if unit and unit.lower() == "k":
        n *= 1_000
    elif unit and unit.lower() == "m":
        n *= 1_000_000
    return n


def extract_count(text: str) -> str:
    """Return the largest 'N unit' dataset-size phrase in the text, or 'N/A'."""
    best = None
    best_n = -1.0
    for value, unit, noun in _COUNT_RE.findall(text):
        n = _numeric(value, unit)
        if n > best_n:
            best_n = n
            suffix = (unit or "")
            best = f"{int(n):,} {noun}" if not suffix else f"{value}{suffix} {noun}"
    return best or "N/A"


# Page assets (JS/CSS/images, embed widgets) are not code/data releases.
_ASSET_RE = re.compile(r"\.(js|css|png|jpe?g|svg|gif|ico|woff2?)$|widgets?\.", re.IGNORECASE)
# Generic HuggingFace path heads that are not a specific repo (badges, nav, the org itself).
_GENERIC_HF = {"huggingface", "papers", "models", "organizations", "login",
               "join", "blog", "docs", "welcome", "new", "settings"}


def _segments(url: str) -> list[str]:
    """Return the non-empty path segments of a URL."""
    m = re.match(r"https?://[^/]+/?(.*)", url)
    return [s for s in (m.group(1) if m else "").split("/") if s]


def _is_real_repo(url: str) -> bool:
    """Reject shallow/generic repo URLs (e.g. a bare org or a HuggingFace badge)."""
    low = url.lower()
    segs = _segments(url)
    if "huggingface.co" in low:
        return len(segs) >= 2 and segs[0] not in _GENERIC_HF
    if any(h in low for h in ("github.com", "gitlab.com", "codeberg.org", "bitbucket.org")):
        return len(segs) >= 2  # require owner/repo, not a bare profile
    return len(segs) >= 1


def find_links(text: str) -> tuple[str, str]:
    """Find the first real code-host and data-host URL in text (skipping assets/badges).

    Returns:
        (code_url, data_url); each is "" if none found.
    """
    code = data = ""
    for m in re.finditer(r"https?://[^\s\"'<>)]+", text):
        url = m.group(0).rstrip(".,);")
        low = url.lower()
        if _ASSET_RE.search(low) or not _is_real_repo(url):
            continue
        if not code and any(h in low for h in CODE_HOSTS):
            code = url
        if not data and any(h in low for h in DATA_HOSTS):
            data = url
    return code, data


def _fetch_text(url: str) -> str:
    """GET a URL and return its text; "" on any failure (gated pages degrade silently)."""
    if not url:
        return ""
    try:
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read(2_000_000).decode("utf-8", errors="ignore")
    except (urllib.error.URLError, ValueError, TimeoutError):
        return ""


def enrich_candidate(candidate: Candidate) -> Candidate:
    """Fill model_field / data_field / count_field on a candidate in place."""
    candidate.count_field = extract_count(candidate.text)

    page = _fetch_text(candidate.landing_url) or _fetch_text(candidate.pdf_url)
    haystack = f"{page} {candidate.text}"
    code, data = find_links(haystack)
    candidate.model_field = f"[Yes]({code})" if code else "N/A"
    candidate.data_field = f"[Yes]({data})" if data else "N/A"
    return candidate


def enrich_all(candidates: list[Candidate]) -> list[Candidate]:
    """Enrich every candidate (network, best-effort)."""
    for c in candidates:
        enrich_candidate(c)
    return candidates
