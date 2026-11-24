"""Tests for the site generator and README linter."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import lint_readme  # noqa: E402
import website_generator as gen  # noqa: E402

README_HEAD = """### Topic Legend
| Label | Topic |
|-------|-------|
| PD | Primate Detection |
| FR | Face Recognition |

### Projects
| Year | Paper | Topic | Animal | Model? | Data? | Image/Video Count |
|------|-----|-------|---------|------------|---------------|-------------|
"""


def test_cells_are_escaped_and_links_converted():
    assert gen.to_link_if_markdown("< 36K") == "&lt; 36K"
    out = gen.to_link_if_markdown('[A & B](https://x.org/a"b)')
    assert out == '<a href="https://x.org/a&quot;b">A &amp; B</a>'


def test_link_with_parentheses_is_not_truncated():
    out = gen.to_link_if_markdown("[Wiki](https://en.wikipedia.org/wiki/Foo_(bar))")
    assert 'href="https://en.wikipedia.org/wiki/Foo_(bar)"' in out


def test_stats_match_on_link_text_not_url():
    df = pd.DataFrame(
        [
            ["2026", "[A](u)", "PD", "Macaque", "[Yes](u)", "[Yes](u)", "N/A"],
            ["2024", "[B](u)", "PD", "Macaque", "[Code only](u)", "N/A", "N/A"],
            ["2011", "[C](u)", "PD", "Macaque", "[No](https://Yes.example)", "[d](https://Yes.example)", "N/A"],
        ]
    )
    stats = gen.calculate_stats(df)
    assert stats == {"total_papers": 3, "years_span": 16, "with_code": 2, "with_data": 1}


def test_build_writes_site_and_badge(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(README_HEAD + "| 2026 | [A](https://doi.org/1) | PD | Macaque | N/A | N/A | N/A |\n")
    gen.build(readme, tmp_path / "out")
    assert "doi.org/1" in (tmp_path / "out" / "index.html").read_text()
    assert '"message": "1"' in (tmp_path / "out" / "stats.json").read_text()


def test_lint_flags_malformed_row_and_unknown_topic(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(
        README_HEAD
        + "| 2026 | [A](https://doi.org/1) | PD | Macaque | N/A | N/A |\n"  # missing a column
        + "| 2025 | [B](https://doi.org/2) | XYZ | Macaque | N/A | N/A | N/A |\n"
    )
    errors, warnings = lint_readme.lint(readme)
    assert len(errors) == 1 and "7-column" in errors[0][1]
    assert any("XYZ" in msg for _, msg in warnings)


def test_repo_readme_has_no_lint_errors():
    errors, _ = lint_readme.lint(Path(__file__).resolve().parents[1] / "README.md")
    assert errors == []


def test_lint_rejects_rows_the_site_would_drop(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(
        README_HEAD
        + "| 2026 | [A](https://doi.org/1) | PD | M | N/A | N/A | N/A |x\n"      # trailing junk
        + "2026 | [B](https://doi.org/2) | PD | M | N/A | N/A | N/A\n"         # no outer pipes
        + "| 2026 | [C](https://doi.org/3) | PD | M | N/A | N/A | N/A |\n"
        + "\n#### Reviews & Related\n| Year | Tag | Topic | Animal |\n|---|---|---|---|\n"
        + "| 2025 | [R](r) | Review | All |\n"
    )
    errors, _ = lint_readme.lint(readme)
    assert sorted(n for n, _ in errors) == [10, 11]
    assert list(gen.extract_table_from_readme(str(readme))["Paper"]) == ["[C](https://doi.org/3)"]
