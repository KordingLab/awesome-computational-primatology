"""Unit tests for the deterministic logic of the Paper Scout (no network)."""

from __future__ import annotations

import dedup
import enrich
import fetch
import judge
import prefilter
import propose
from dedup import Entry
from fetch import Candidate


def _cand(**kw) -> Candidate:
    """Build a Candidate with sensible defaults for tests."""
    base = dict(source="openalex", title="", abstract="", doi="", arxiv_id="",
                date="2026-04-01", venue="", authors=[])
    base.update(kw)
    return Candidate(**base)


# ---- fetch -----------------------------------------------------------------

def test_reconstruct_abstract_orders_words():
    inverted = {"deep": [0], "learning": [1], "macaque": [2]}
    assert fetch._reconstruct_abstract(inverted) == "deep learning macaque"
    assert fetch._reconstruct_abstract(None) == ""


def test_norm_doi_strips_scheme_and_lowercases():
    assert fetch._norm_doi("https://doi.org/10.1234/ABC") == "10.1234/abc"
    assert fetch._norm_doi(None) == ""


def test_work_key_prefers_arxiv_then_doi_then_title():
    assert _cand(arxiv_id="2410.17136", doi="10.1/x").work_key == "arxiv:2410.17136"
    assert _cand(doi="10.1/x").work_key == "doi:10.1/x"
    assert _cand(title="A B!").work_key == "title:ab"


def test_dedup_by_title_prefers_doi_copy():
    a = _cand(title="Same Paper Title", source="arxiv", arxiv_id="2601.1")
    b = _cand(title="Same Paper Title!", source="openalex", doi="10.1/x")
    out = fetch._dedup_by_title([a, b])
    assert len(out) == 1 and out[0].doi == "10.1/x"


# ---- dedup -----------------------------------------------------------------

def test_tool_token_excludes_author_style():
    assert dedup._tool_token("Mueller et al.") == ""
    assert dedup._tool_token("Loos & Ernst") == ""
    assert dedup._tool_token("Tri-A") == ""           # single short token dropped
    assert dedup._tool_token("AlphaChimp") == "alphachimp"
    assert dedup._tool_token("PRIMAT (Vogg et al.)") == "primat"
    assert dedup._tool_token("APT-36K") == "apt 36k"


def test_contains_phrase_is_whole_word_not_substring():
    assert dedup._contains_phrase("PriMAT: Robust tracking", "primat")
    assert not dedup._contains_phrase("primate behavior dataset", "primat")  # the bug we fixed
    assert dedup._contains_phrase("APT-36K dataset release", "apt 36k")
    assert not dedup._contains_phrase("apt big 36k", "apt 36k")              # not contiguous


def test_id_from_url():
    assert dedup._id_from_url("https://doi.org/10.1/X.")[0] == "10.1/x"
    assert dedup._id_from_url("https://doi.org/10.48550/arXiv.2410.17136")[1] == "2410.17136"


def test_classify_three_way():
    index = [
        Entry(name="AlphaChimp", year="2024", doi="10.48550/arxiv.2410.17136",
              arxiv_id="2410.17136", tool_token="alphachimp", cells=[]),
    ]
    skip = dedup.classify(_cand(arxiv_id="2410.17136"), index)
    update = dedup.classify(_cand(title="AlphaChimp: journal version", doi="10.1/new"), index)
    new = dedup.classify(_cand(title="A wholly different macaque pose paper", doi="10.9/z"), index)
    assert skip.classification == "SKIP"
    assert update.classification == "UPDATE" and update.update_target == "AlphaChimp"
    assert new.classification == "NEW"


# ---- prefilter -------------------------------------------------------------

def test_rules_require_animal_and_method():
    assert prefilter.passes_rules("macaque pose estimation with a CNN")[0]
    assert not prefilter.passes_rules("macaque foraging ecology in the wild")[0]  # no method
    assert not prefilter.passes_rules("human face recognition benchmark")[0]      # no primate


def test_rules_flag_tangent():
    _, tangent = prefilter.passes_rules("modeling macaque visual cortex with a deep network")
    assert tangent


# ---- judge -----------------------------------------------------------------

def test_parse_verdict_clean_json():
    v = judge.parse_verdict('{"decision":"KEEP","score":0.9,"reason":"r","animal":"Macaque","topic_tags":["FR"]}')
    assert v["decision"] == "KEEP" and v["score"] == 0.9 and v["topic_tags"] == ["FR"]


def test_parse_verdict_tolerates_prose_and_bad_fields():
    v = judge.parse_verdict('Sure!\n{"decision":"maybe","score":"x"}\nthanks')
    assert v["decision"] == "REVIEW"   # invalid decision -> REVIEW
    assert v["score"] == 0.0           # unparsable score -> 0.0
    assert v["animal"] == "N/A"


def test_decision_from_score_thresholds():
    assert judge.decision_from_score(0.8) == "KEEP"
    assert judge.decision_from_score(0.5) == "REVIEW"
    assert judge.decision_from_score(0.2) == "REJECT"


# ---- enrich ----------------------------------------------------------------

def test_extract_count_picks_largest():
    assert enrich.extract_count("we used 3,385 images from 18 individuals") == "3,385 images"
    assert enrich.extract_count("trained on 20k videos and 5 clips") == "20k videos"
    assert enrich.extract_count("no numbers here") == "N/A"


def test_find_links_separates_code_and_data():
    text = "code at https://github.com/foo/bar and data at https://zenodo.org/record/123."
    code, data = enrich.find_links(text)
    assert code == "https://github.com/foo/bar"
    assert data == "https://zenodo.org/record/123"


def test_find_links_skips_page_assets():
    # A figshare JS widget is not a dataset release.
    code, data = enrich.find_links("badge https://widgets.figshare.com/static/figshare.js")
    assert data == ""


def test_find_links_rejects_generic_and_shallow_repos():
    # Generic HuggingFace badge / bare github profile are not real repos.
    assert enrich.find_links("see https://huggingface.co/huggingface")[0] == ""
    assert enrich.find_links("see https://github.com/someuser")[0] == ""
    # A real owner/repo is kept.
    assert enrich.find_links("https://github.com/ecker-lab/PriMAT-tracking")[0].endswith("PriMAT-tracking")


# ---- propose ---------------------------------------------------------------

def test_make_name_and_url():
    c = _cand(title="AlphaChimp: Tracking Chimpanzees", doi="10.1/x")
    assert propose.make_name(c) == "AlphaChimp"
    assert propose.make_url(c) == "https://doi.org/10.1/x"
    c2 = _cand(title="A study with no colon", authors=["Jane Q. Mueller"], arxiv_id="2601.1")
    assert propose.make_name(c2) == "Mueller et al."
    assert propose.make_url(c2) == "https://doi.org/10.48550/arXiv.2601.1"


def test_make_row_format():
    c = _cand(title="X: y", doi="10.1/x", animal="Macaque", topic_tags=["FR"],
              model_field="N/A", data_field="N/A", count_field="3,385 images")
    row = propose.make_row(c)
    assert row == "| 2026 | [X](https://doi.org/10.1/x) | FR | Macaque | N/A | N/A | 3,385 images |"


def test_set_badge_updates_count():
    text = "[![Papers](https://img.shields.io/badge/Papers-90-blue)](#projects)"
    assert "Papers-96-blue" in propose.set_badge(text, 96)
    assert "Papers-90" not in propose.set_badge(text, 96)


def test_insert_rows_after_separator():
    readme = "### Projects\n\n| Year | Paper |\n|------|-------|\n| 2025 | old |\n"
    out = propose.insert_rows(readme, ["| 2026 | new |"])
    lines = out.splitlines()
    sep = next(i for i, l in enumerate(lines) if l.startswith("|---") or l.startswith("|--"))
    assert lines[sep + 1] == "| 2026 | new |"
    assert lines[sep + 2] == "| 2025 | old |"


def test_apply_update_swaps_link_and_year():
    cells = ["2024", "[AlphaChimp](https://doi.org/10.48550/arXiv.2410.17136)",
             "PD, BR", "Chimp", "[Yes](g)", "[d](z)", "N/A"]
    readme = "| " + " | ".join(cells) + " |\n"
    entry = Entry(name="AlphaChimp", year="2024", doi="", arxiv_id="2410.17136",
                  tool_token="alphachimp", cells=cells)
    c = _cand(title="AlphaChimp journal", doi="10.1007/s11263-026-02867-3", date="2026-05-01")
    out = propose.apply_update(readme, entry, c)
    assert "2026" in out and "10.1007/s11263-026-02867-3" in out
    assert "PD, BR" in out and "[Yes](g)" in out   # other cells inherited
    assert "arXiv.2410.17136" not in out           # old link replaced
