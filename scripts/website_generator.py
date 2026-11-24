#!/usr/bin/env python3
"""Build the static site from the README table.

Writes, into the output directory (default: ``_site/``):
  index.html  the searchable list (template: scripts/site_template.html)
  papers.csv  the table as CSV
  stats.json  a shields.io endpoint for the README's paper-count badge

The growth figure is drawn separately by ``scripts/plot_paper_growth.py`` into
``<out>/assets/``. None of these are committed; CI builds and deploys them.

Usage:
    python scripts/website_generator.py [--out _site]
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


REPO_ROOT = Path(__file__).resolve().parent.parent

# [text](url), where url may contain one level of balanced parentheses (e.g. Wikipedia-style).
MD_LINK = re.compile(r"\[([^\]]*)\]\(((?:[^()\s]|\([^()\s]*\))+)\)")


def to_link_if_markdown(cell_text: str) -> str:
    """Convert a README cell to HTML: escape text, turn markdown links into <a> tags."""
    if not isinstance(cell_text, str):
        cell_text = str(cell_text)
    out, pos = [], 0
    for m in MD_LINK.finditer(cell_text):
        out.append(html.escape(cell_text[pos:m.start()]))
        out.append(f'<a href="{html.escape(m.group(2), quote=True)}">{html.escape(m.group(1))}</a>')
        pos = m.end()
    out.append(html.escape(cell_text[pos:]))
    return "".join(out).strip()


def link_text(cell_text: str) -> str:
    """Return a cell's visible text: "[Yes](url)" -> "Yes"."""
    return MD_LINK.sub(lambda m: m.group(1), cell_text).strip()

COLUMNS = ["Year", "Paper", "Topic", "Animal", "Model?", "Data?", "Image/Video Count"]
_SEPARATOR = re.compile(r"^\|(\s*:?-+:?\s*\|)+$")


def iter_paper_rows(lines: list[str]):
    """Yield (line_number, cells or None, raw_line) for every table line of the paper tables.

    The paper tables are the "### Projects" table and its "#### Dataset ..."
    sub-table; scanning stops at "#### Reviews & Related" or the next "##"/"###"
    heading. Header and separator lines are skipped. cells is None when a
    table-like line is not a well-formed 7-column "| ... |" row; the linter
    reports those and the site skips them. Shared by the generator, the linter
    and the growth plot so all three agree on what counts as a paper.
    """
    inside = False
    for n, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped == "### Projects":
            inside = True
            continue
        if not inside:
            continue
        if stripped.startswith("#"):
            if "Reviews" in stripped or not stripped.startswith("####"):
                return
            continue
        if "|" not in stripped or _SEPARATOR.match(stripped):
            continue
        if not (stripped.startswith("|") and stripped.endswith("|")):
            yield n, None, stripped
            continue
        cells = [c.strip() for c in stripped[1:-1].split("|")]
        if cells[0] == "Year":
            continue
        yield n, (cells if len(cells) == len(COLUMNS) else None), stripped


def extract_table_from_readme(readme_path: str) -> pd.DataFrame:
    """Return the well-formed paper rows of README.md as raw markdown cells.

    Raises:
        ValueError: If no rows are found.
    """
    import pandas as pd  # lazy: the linter shares this module and needs only the stdlib

    lines = Path(readme_path).read_text(encoding="utf-8").splitlines()
    data = [cells for _, cells, _ in iter_paper_rows(lines) if cells is not None]
    if not data:
        raise ValueError("Could not find valid table in README.md")
    return pd.DataFrame(data, columns=COLUMNS)


TEMPLATE = Path(__file__).resolve().parent / "site_template.html"

# Short, human labels for the topic codes (the README legend keeps the long names).
TOPIC_SHORT = {
    "PD": "Detection", "BPE": "Body pose", "FD": "Face detection", "FLE": "Face landmarks",
    "FR": "Face ID", "FAC": "Facial action", "HD": "Hand detection", "HPE": "Hand pose",
    "BR": "Behavior", "AM": "Avatar / mesh", "SI": "Species ID", "RL": "RL",
    "AV": "Vocalization", "O": "Other",
}
# Species groups for the filter; a row can belong to several. Order = display priority.
SPECIES_GROUPS = [
    ("macaque", "Macaques", ("macaque", "rhesus")),
    ("chimpanzee", "Chimpanzees", ("chimp",)),
    ("gorilla", "Gorillas", ("gorilla",)),
    ("bonobo", "Bonobos", ("bonobo",)),
    ("orangutan", "Orangutans", ("orangutan",)),
    ("ape", "Great apes (mixed)", ("ape",)),
    ("marmoset", "Marmosets", ("marmoset",)),
    ("lemur", "Lemurs", ("lemur",)),
    ("gibbon", "Gibbons", ("gibbon",)),
    ("baboon", "Baboons", ("baboon",)),
    ("capuchin", "Capuchins", ("capuchin",)),
    ("howler", "Howler monkeys", ("howler",)),
    ("cross", "Many species", ("cross", "species", "nhp", "any", "multiple", "all")),
]
EMPTY = {"", "N/A", "TBD", "No"}


def topic_legend(lines: list[str]) -> dict[str, str]:
    """Topic code -> long name, from the README's "### Topic Legend" table."""
    legend, inside = {}, False
    for line in lines:
        if line.strip().startswith("### Topic Legend"):
            inside = True
            continue
        if inside:
            if line.startswith("#"):
                break
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == 2 and cells[0] not in ("Label", "") and not set(cells[0]) <= set("-: "):
                legend[cells[0]] = cells[1]
    return legend


def species_of(animal: str) -> list[str]:
    a = animal.lower()
    keys = [key for key, _, words in SPECIES_GROUPS if any(w in a for w in words)]
    if "ape" in keys and len(keys) > 1:  # "Great Ape" is informative only when nothing more specific matched
        keys.remove("ape")
    return keys or ["other"]


def _topic_families(topic: str) -> list[str]:
    """ "2D BPE, FR" -> ["BPE", "FR"] (dimension prefixes fold into the base code)."""
    fams = []
    for t in (t.strip() for t in topic.split(",")):
        if t:
            base = t.split()[-1]
            fams.append(base if base in TOPIC_SHORT else t)
    return list(dict.fromkeys(fams))


def _resource(cell: str, kind: str) -> str:
    """Render a Model?/Data? cell as a quiet pill link (or muted text)."""
    m = MD_LINK.search(cell)
    text = link_text(cell)
    if text in EMPTY and not (m and text == "No"):
        return ""
    if kind == "model":
        label = {"Yes": "Code + models", "Code only": "Code", "No": "Repo"}.get(text, text)
    else:
        label = {"Yes": "Data"}.get(text, text)
        if text == "Upon request":
            label = "Data on request"
    esc = html.escape(label)
    if m:
        return f'<a class="res" href="{html.escape(m.group(2), quote=True)}">{esc}</a>'
    return f'<span class="res muted">{esc}</span>'


def render_paper(cells: list[str], legend: dict[str, str]) -> str:
    year, paper, topic, animal, model, data, count = cells
    link = MD_LINK.search(paper)
    name = link.group(1) if link else link_text(paper)
    url = link.group(2) if link else ""
    fams = _topic_families(topic)
    tags = "".join(
        f'<span class="tag" title="{html.escape(legend.get(f, f))}">{html.escape(TOPIC_SHORT.get(f, f))}</span>'
        for f in fams
    )
    meta = tags + f'<span class="dot">{html.escape(animal)}</span>'
    if link_text(count) not in EMPTY:
        meta += f'<span class="dot count">{html.escape(link_text(count))}</span>'
    resources = _resource(model, "model") + _resource(data, "data")
    has_code = link_text(model) in ("Yes", "Code only")
    has_data = link_text(data) == "Yes"
    search = " ".join([year, name, topic, " ".join(TOPIC_SHORT.get(f, "") for f in fams),
                       " ".join(legend.get(f, "") for f in fams), animal, link_text(count)]).lower()
    title = (f'<a class="p-title" href="{html.escape(url, quote=True)}">{html.escape(name)}</a>'
             if url else f'<span class="p-title">{html.escape(name)}</span>')
    return (
        f'<li class="paper" data-year="{html.escape(year)}" data-topics="{html.escape(" ".join(fams))}" '
        f'data-species="{" ".join(species_of(animal))}" data-code="{int(has_code)}" data-data="{int(has_data)}" '
        f'data-text="{html.escape(search, quote=True)}">'
        f'<div class="p-year">{html.escape(year)}</div>'
        f'<div class="p-main">{title}<div class="p-meta">{meta}</div></div>'
        f'<div class="p-links">{resources}</div></li>'
    )


def review_rows(lines: list[str]) -> list[list[str]]:
    """Rows of the 4-column "#### Reviews & Related" table."""
    rows, inside = [], False
    for line in lines:
        s = line.strip()
        if s.startswith("#"):
            inside = "Reviews" in s
            continue
        if inside and s.startswith("|") and s.endswith("|") and not _SEPARATOR.match(s):
            cells = [c.strip() for c in s[1:-1].split("|")]
            if len(cells) == 4 and cells[0] != "Year":
                rows.append(cells)
    return rows


def render_review(cells: list[str]) -> str:
    year, tag, what, animal = cells
    m = MD_LINK.search(tag)
    name = html.escape(m.group(1) if m else tag)
    title = f'<a href="{html.escape(m.group(2), quote=True)}">{name}</a>' if m else name
    return (f'<li><span class="p-year">{html.escape(year)}</span>'
            f'<span>{title} <span class="what">· {html.escape(what)}</span></span></li>')


def calculate_stats(df: pd.DataFrame) -> dict:
    """Headline numbers for the stat strip and badge, from the raw markdown cells.

    "with code" counts Model? = Yes or Code only; "with data" counts Data? = Yes,
    matched on the link text so URLs containing "Yes" cannot inflate counts.
    """
    years = sorted({int(y) for y in df.iloc[:, 0] if str(y).isdigit()})
    model = df.iloc[:, 4].map(link_text)
    data = df.iloc[:, 5].map(link_text)
    return {
        "total_papers": len(df),
        "years_span": years[-1] - years[0] + 1 if years else 0,
        "with_code": int(model.isin(["Yes", "Code only"]).sum()),
        "with_data": int((data == "Yes").sum()),
    }


def last_updated(readme_path: Path) -> str:
    """Date of the last commit touching the README (falls back to today)."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", readme_path.name],
            cwd=readme_path.parent, capture_output=True, text=True, check=True,
        ).stdout.strip()
        day = dt.date.fromisoformat(out) if out else dt.date.today()
    except (OSError, subprocess.CalledProcessError, ValueError):
        day = dt.date.today()
    return f"{day:%B} {day.day}, {day.year}"


def build(readme_path: Path, out_dir: Path) -> dict:
    """Render index.html, papers.csv and stats.json into out_dir; return the stats."""
    import csv

    lines = readme_path.read_text(encoding="utf-8").splitlines()
    raw = extract_table_from_readme(str(readme_path))
    stats = calculate_stats(raw)
    legend = topic_legend(lines)

    # Which rows belong to the cross-species dataset sub-table.
    papers, datasets, in_datasets = [], [], False
    rows = {n: cells for n, cells, _ in iter_paper_rows(lines) if cells is not None}
    for n, line in enumerate(lines, 1):
        if line.strip().startswith("####"):
            in_datasets = "Dataset" in line
        if n in rows:
            (datasets if in_datasets else papers).append(rows[n])

    fams = {f for cells in papers + datasets for f in _topic_families(cells[2])}
    chips = "".join(
        f'<button class="chip" data-topic="{code}" aria-pressed="false" title="{html.escape(legend.get(code, code))}">'
        f"{html.escape(short)}</button>"
        for code, short in TOPIC_SHORT.items() if code in fams
    )
    counts: dict[str, int] = {}
    for cells in papers + datasets:
        for key in species_of(cells[3]):
            counts[key] = counts.get(key, 0) + 1
    labels = {key: label for key, label, _ in SPECIES_GROUPS} | {"other": "Other primates"}
    options = "".join(
        f'<option value="{key}">{html.escape(labels[key])} ({n})</option>'
        for key, n in sorted(counts.items(), key=lambda kv: (-kv[1], labels[kv[0]]))
    )
    years = sorted(int(c[0]) for c in papers + datasets if c[0].isdigit())
    values = {
        **{k: str(v) for k, v in stats.items()},
        "first_year": str(years[0]) if years else "",
        "last_year": str(years[-1]) if years else "",
        "topic_chips": chips,
        "species_options": options,
        "papers": "\n".join(render_paper(c, legend) for c in papers),
        "datasets": "\n".join(render_paper(c, legend) for c in datasets),
        "reviews": "\n".join(render_review(c) for c in review_rows(lines)),
        "last_updated": last_updated(readme_path),
    }
    page = re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], TEMPLATE.read_text(encoding="utf-8"))

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(page, encoding="utf-8")
    with open(out_dir / "papers.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["year", "name", "url", "topics", "animal", "model", "model_url", "data", "data_url", "count"])
        for c in papers + datasets:
            link, ml, dl = MD_LINK.search(c[1]), MD_LINK.search(c[4]), MD_LINK.search(c[5])
            w.writerow([c[0], link_text(c[1]), link.group(2) if link else "", c[2], c[3],
                        link_text(c[4]), ml.group(2) if ml else "", link_text(c[5]), dl.group(2) if dl else "",
                        link_text(c[6])])
    badge = {"schemaVersion": 1, "label": "Papers", "message": str(stats["total_papers"]), "color": "2f7a52"}
    (out_dir / "stats.json").write_text(json.dumps({**badge, "stats": stats}, indent=2) + "\n", encoding="utf-8")
    return stats


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--readme", type=Path, default=REPO_ROOT / "README.md")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "_site")
    args = ap.parse_args()
    stats = build(args.readme, args.out)
    print(f"Rows: {stats['total_papers']}  stats: {stats}")
    print(f"Wrote {args.out / 'index.html'} and {args.out / 'stats.json'}")


if __name__ == "__main__":
    main()
