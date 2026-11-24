#!/usr/bin/env python3
"""Plot the growth of computational primatology papers, xkcd-style.

Produces a two-panel figure:
  1. Papers curated in this awesome-list, per year (parsed from README.md).
  2. The raw firehose of "primate + machine learning" papers on OpenAlex,
     per year (fetched live, with a cached fallback).

The contrast motivates the need for an automated, *selective* scout: the
field's output is exploding while a hand-curated list can only grow linearly.

Not committed: CI draws it into the built site (``_site/assets/``) on every
deploy and weekly, so the live OpenAlex panel stays current.

Usage:
    python scripts/plot_paper_growth.py [--out _site/assets/paper_growth.png]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.parse
import urllib.request
import warnings
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import MaxNLocator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from website_generator import extract_table_from_readme  # noqa: E402  (same row parser as the site)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
README_PATH = PROJECT_ROOT / "README.md"
CURRENT_YEAR = dt.date.today().year  # plotted as a partial (year-to-date) point
OUTPUT_PATH = PROJECT_ROOT / "_site" / "assets" / "paper_growth.png"
# xkcd-style fonts in preference order (CI installs Humor Sans via apt `fonts-humor-sans`).
XKCD_FONTS = ["xkcd", "xkcd Script", "Humor Sans", "Comic Neue", "Comic Sans MS"]

# Cached OpenAlex counts (fetched 2026-11-24; complete years only) used if the live request fails.
# NOTE: this is a *broad keyword* search ("primate + ML"), not a clean field
# definition. It over-counts: it pulls in foundational CV (e.g. GoogLeNet),
# surveys, and primate-visual-cortex-as-ML-model papers. We plot it precisely
# to show how noisy the unfiltered firehose is -- the motivation for a judge.
OPENALEX_FALLBACK: dict[int, int] = {
    2011: 129, 2012: 143, 2013: 161, 2014: 181, 2015: 208, 2016: 304, 2017: 293,
    2018: 330, 2019: 387, 2020: 455, 2021: 562, 2022: 540, 2023: 778,
    2024: 921, 2025: 1140,
}


def curated_counts_by_year() -> dict[int, int]:
    """Count listed papers by publication year.

    Uses the website generator's parser, so the figure counts exactly the rows the
    site and badge count (the Projects + dataset tables, not "Reviews & Related").

    Returns:
        Mapping of year to number of curated papers in that year.
    """
    df = extract_table_from_readme(str(README_PATH))
    years = [int(y) for y in df.iloc[:, 0] if str(y).isdigit()]
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
            groups = json.load(resp)["group_by"]
        counts = {int(g["key"]): g["count"] for g in groups if g["key"].isdigit()}
        return {y: c for y, c in sorted(counts.items()) if 2011 <= y <= CURRENT_YEAR}
    except Exception as exc:  # noqa: BLE001 - network is best-effort here
        print(f"OpenAlex fetch failed ({exc}); using cached fallback.", file=sys.stderr)
        return OPENALEX_FALLBACK


def _plot_with_partial_year(ax, series: dict[int, int], color: str) -> None:
    """Plot complete years solid; draw the current (incomplete) year hollow and dashed."""
    full = {y: c for y, c in series.items() if y < CURRENT_YEAR}
    ax.plot(list(full), list(full.values()), marker="o", color=color, zorder=3)
    if CURRENT_YEAR in series and full:
        last = max(full)
        ax.plot([last, CURRENT_YEAR], [full[last], series[CURRENT_YEAR]],
                linestyle="--", marker="o", markevery=[1], markerfacecolor="white", color=color, zorder=2)
        ax.annotate(f"{CURRENT_YEAR}\n(so far)", xy=(CURRENT_YEAR, series[CURRENT_YEAR]),
                    xytext=(-58, -30), textcoords="offset points", fontsize=9)


def _xkcd_font() -> str | None:
    """Return the first installed xkcd-style font family, if any."""
    installed = {f.name for f in font_manager.fontManager.ttflist}
    return next((name for name in XKCD_FONTS if name in installed), None)


def main() -> None:
    """Generate and save the xkcd-style growth figure."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=OUTPUT_PATH)
    args = ap.parse_args()

    curated = curated_counts_by_year()
    field = openalex_counts_by_year()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    font = _xkcd_font()
    if font is None:
        print("No xkcd-style font installed (apt: fonts-humor-sans); using the default.", file=sys.stderr)

    # plt.xkcd() probes a fixed font list and warns once per glyph for each missing family;
    # pin the family to one that exists instead.
    with plt.xkcd(), warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="findfont")
        if font:
            plt.rcParams["font.family"] = [font]
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

        _plot_with_partial_year(ax1, curated, "#2b6cb0")
        ax1.set_title("Papers in THIS list\n(hand-curated)")
        ax1.set_xlabel("year")
        ax1.set_ylabel("# papers (by publication year)")
        # No such thing as half a paper -> integer ticks only.
        ax1.yaxis.set_major_locator(MaxNLocator(integer=True))

        _plot_with_partial_year(ax2, field, "#c53030")
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
        fig.savefig(args.out, dpi=130, bbox_inches="tight")

    print(f"Curated by year: {curated}")
    print(f"Field by year:   {field}")
    print(f"Saved: {args.out}")


if __name__ == "__main__":
    main()
