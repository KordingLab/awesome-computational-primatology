#!/usr/bin/env python3
"""Plot the growth of computational primatology papers, xkcd-style.

Produces a two-panel figure:
  1. Papers curated in this awesome-list, per year (parsed from README.md).
  2. The raw firehose of "primate + machine learning" papers on OpenAlex,
     per year (fetched live, with a cached fallback).

The contrast motivates the need for an automated, *selective* scout: the
field's output is exploding while a hand-curated list can only grow linearly.

Usage:
    python scripts/plot_paper_growth.py
"""

from __future__ import annotations

import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
README_PATH = PROJECT_ROOT / "README.md"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "assets" / "paper_growth_xkcd.png"

# Cached OpenAlex counts (fetched 2026-05) used if the live request fails.
# NOTE: this is a *broad keyword* search ("primate + ML"), not a clean field
# definition. It over-counts: it pulls in foundational CV (e.g. GoogLeNet),
# surveys, and primate-visual-cortex-as-ML-model papers. We plot it precisely
# to show how noisy the unfiltered firehose is -- the motivation for a judge.
OPENALEX_FALLBACK: dict[int, int] = {
    2011: 82, 2012: 87, 2013: 119, 2014: 122, 2015: 122, 2016: 187, 2017: 185,
    2018: 233, 2019: 289, 2020: 332, 2021: 453, 2022: 435, 2023: 840,
    2024: 816, 2025: 791,
}


def curated_counts_by_year() -> dict[int, int]:
    """Count papers in README.md by publication year.

    Returns:
        Mapping of year to number of curated papers in that year.
    """
    text = README_PATH.read_text(encoding="utf-8")
    years = [int(y) for y in re.findall(r"^\|\s*(\d{4})\s*\|", text, re.MULTILINE)]
    return dict(sorted(Counter(years).items()))


def openalex_counts_by_year() -> dict[int, int]:
    """Fetch per-year counts of 'primate + ML' papers from OpenAlex.

    Returns:
        Mapping of year to OpenAlex work count, or the cached fallback if the
        network request fails.
    """
    params = urllib.parse.urlencode(
        {
            "search": "primate deep learning pose estimation",
            "group_by": "publication_year",
            "mailto": "parodifelipe07@gmail.com",
        }
    )
    url = f"https://api.openalex.org/works?{params}"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            import json

            groups = json.load(resp)["group_by"]
        counts = {int(g["key"]): g["count"] for g in groups if g["key"].isdigit()}
        return {y: c for y, c in sorted(counts.items()) if 2011 <= y <= 2025}
    except Exception as exc:  # noqa: BLE001 - network is best-effort here
        print(f"OpenAlex fetch failed ({exc}); using cached fallback.", file=sys.stderr)
        return OPENALEX_FALLBACK


def main() -> None:
    """Generate and save the xkcd-style growth figure."""
    curated = curated_counts_by_year()
    field = openalex_counts_by_year()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with plt.xkcd():
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

        ax1.plot(list(curated), list(curated.values()), marker="o", color="#2b6cb0")
        ax1.set_title("Papers in THIS list\n(hand-curated)")
        ax1.set_xlabel("year")
        ax1.set_ylabel("# papers added")
        # No such thing as half a paper -> integer ticks only.
        ax1.yaxis.set_major_locator(MaxNLocator(integer=True))

        ax2.plot(list(field), list(field.values()), marker="o", color="#c53030")
        ax2.set_title('"primate + ML" keyword firehose\n(OpenAlex, mostly tangential)')
        ax2.set_xlabel("year")
        ax2.set_ylabel("# keyword matches")
        ax2.annotate(
            "incl. GoogLeNet,\ncortex models, surveys...\n(noise a judge must reject)",
            xy=(2023, field.get(2023, max(field.values()))),
            xytext=(2011.5, max(field.values()) * 0.62),
            arrowprops=dict(arrowstyle="->"),
            fontsize=9,
        )

        fig.suptitle("Why computational primatology needs a scout", fontsize=15)
        fig.tight_layout()
        fig.savefig(OUTPUT_PATH, dpi=130, bbox_inches="tight")

    print(f"Curated by year: {curated}")
    print(f"Field by year:   {field}")
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
