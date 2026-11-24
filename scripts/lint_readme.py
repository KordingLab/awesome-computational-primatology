#!/usr/bin/env python3
"""Lint the README paper tables.

Errors (always fail): rows that the site generator would silently drop or
mangle -- wrong column count, non-numeric year, a paper cell without a link.

Warnings (fail only with --strict): vocabulary and hygiene -- topic codes not in
the Topic Legend, Model?/Data? values outside the legend, duplicate links,
rows out of newest-first year order.

Prints GitHub Actions annotations, so problems show inline on the PR diff.

Usage:
    python scripts/lint_readme.py [--strict] [README.md]
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from website_generator import MD_LINK, iter_paper_rows  # noqa: E402  (one row parser for site + lint)

SEPARATOR = re.compile(r"^\|(\s*:?-+:?\s*\|)+\s*$")
# Model?/Data? values the legends allow, matched on the visible (link) text.
MODEL_VALUES = {"Yes", "Code only", "No", "N/A", "Upon request"}
DATA_VALUES = {"Yes", "No", "N/A", "Upon request"}


def legend_codes(lines: list[str]) -> set[str]:
    """Topic codes defined in the README's "Topic Legend" table."""
    codes, inside = set(), False
    for line in lines:
        if line.strip().startswith("### Topic Legend"):
            inside = True
            continue
        if inside:
            if line.startswith("#"):
                break
            m = re.match(r"^\|\s*([^|]+?)\s*\|", line)
            if m and m.group(1) not in {"Label"} and not SEPARATOR.match(line):
                codes.add(m.group(1))
    return codes


def visible(cell: str) -> str:
    return MD_LINK.sub(lambda m: m.group(1), cell).strip()


def lint(path: Path) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    """Return (errors, warnings) as (line number, message) pairs."""
    lines = path.read_text(encoding="utf-8").splitlines()
    codes = legend_codes(lines)
    errors: list[tuple[int, str]] = []
    warnings: list[tuple[int, str]] = []
    links: dict[str, list[int]] = defaultdict(list)

    prev_year, prev_line = None, 0
    for n, cells, raw in iter_paper_rows(lines):
        if cells is None:
            errors.append((n, "not a 7-column '| ... |' row (check for a stray, missing or outer '|'); "
                              "the site would drop it"))
            continue
        if n != prev_line + 1:
            prev_year = None  # a new table (the dataset sub-table) restarts the ordering
        prev_line = n
        year, paper, topic, _animal, model, data, _count = cells
        if not re.fullmatch(r"\d{4}", year):
            errors.append((n, f"year must be four digits, got {year!r}"))
            continue
        link = MD_LINK.search(paper)
        if not link:
            errors.append((n, f"paper cell needs a [Name](url) link, got {paper!r}"))
        else:
            links[link.group(2).rstrip("/").lower()].append(n)

        unknown = [t for t in (t.strip() for t in topic.split(",")) if t and t not in codes]
        if unknown:
            warnings.append((n, f"topic code(s) not in the Topic Legend: {', '.join(unknown)}"))
        if visible(model) not in MODEL_VALUES:
            warnings.append((n, f"Model? value {visible(model)!r} is not one of {sorted(MODEL_VALUES)}"))
        if visible(data) not in DATA_VALUES and not MD_LINK.search(data):
            warnings.append((n, f"Data? value {visible(data)!r} is neither a link nor one of {sorted(DATA_VALUES)}"))
        if prev_year is not None and int(year) > prev_year:
            warnings.append((n, f"{year} row below a {prev_year} row (table is newest-first)"))
        prev_year = int(year)

    for url, where in links.items():
        if len(where) > 1:
            for n in where:
                warnings.append((n, f"same paper link as line(s) {', '.join(str(w) for w in where if w != n)}: {url}"))
    return errors, sorted(warnings)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("readme", nargs="?", type=Path, default=REPO_ROOT / "README.md")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args()

    errors, warnings = lint(args.readme)
    rel = args.readme.resolve().relative_to(REPO_ROOT) if args.readme.resolve().is_relative_to(REPO_ROOT) else args.readme
    warn_level = "error" if args.strict else "warning"
    for n, msg in errors:
        print(f"::error file={rel},line={n}::{msg}")
    for n, msg in warnings:
        print(f"::{warn_level} file={rel},line={n}::{msg}")
    failed = bool(errors) or (args.strict and bool(warnings))
    print(f"{len(errors)} error(s), {len(warnings)} warning(s){' (strict)' if args.strict else ''}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
