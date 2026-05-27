# Paper Scout — Design Spec

A weekly, self-sustaining agent that finds **hyper-relevant** new computational-primatology
papers and proposes them as a **draft PR** to `README.md`. Human stays in the loop: the agent
never merges, it only nominates.

Status: **implemented** in `scripts/scout/` (tests in `tests/scout/`, workflow
`.github/workflows/paper-scout.yml`). Goes live once the `GROQ_API_KEY` repo secret is set.
Decisions locked (2026-05-27):

| Decision | Choice |
|---|---|
| Delivery | Draft PR with ready-to-merge table rows |
| Relevance gate | Embedding prefilter → LLM judge (two-stage) |
| Runtime | GitHub Actions weekly cron |
| Judge model | Free **open-weight** LLM via hosted API (Groq); Gemini-free fallback |
| Embeddings | `all-MiniLM-L6-v2` run **locally in the Action** (no API) |
| Human role | Review + merge/close the PR |

## Why two stages (the whole point)

A single keyword query is hopelessly noisy. Live proof from OpenAlex: searching
`primate + deep learning + pose estimation` returns ~5,800 works whose top hits include
*GoogLeNet*, *"Event-Based Vision: A Survey"*, and primate-**cortex**-as-ML-model papers — none
are computational primatology of animals. See `scripts/plot_paper_growth.py` /
`docs/assets/paper_growth_xkcd.png`. So:

1. **Cheap prefilter** kills the obvious tangents for free (embeddings + rules).
2. **LLM judge** applies a written rubric to the survivors, with a justification per paper.

## Prior art (fork the loop, not the sources)

The cron-Action + LLM-rating loop is well-trodden; reuse it, don't reinvent it:

- [AutoLLM/ArxivDigest](https://github.com/AutoLLM/ArxivDigest) — canonical: GH Action pulls
  arXiv abstracts, LLM rates relevance 1–10 vs an interest description, emails a digest.
- [ArxivDigest-extra](https://github.com/linhkid/ArxivDigest-extra) — multi-model (OpenAI/
  Gemini/Claude) + topic clustering.
- [TideDra/zotero-arxiv-daily](https://github.com/TideDra/zotero-arxiv-daily) — zero-cost GH
  Action seeded by a Zotero library (the seed-papers approach).
- [matouskozak/arxiv-digest](https://github.com/tb5z035i/arxiv-digest) — delivers into GitHub
  Issues (closest to our in-repo delivery).

**What we add (why a fork isn't enough):** all of the above are *arXiv-only* and emit
email/issues. Since ~74% of this corpus is off arXiv, we keep their proven mechanics but
replace the source layer with multi-source fetch (OpenAlex/Crossref/PubMed) and the delivery
layer with a draft PR against this awesome-list.

## Pipeline

```
GitHub Actions (cron: weekly, Monday 08:00 UTC)
  │
  1. FETCH (last ~10 days, keyless where possible)
  │    • OpenAlex      group/filter by publication_date, animal+method terms
  │    • arXiv API     cs.CV / q-bio.NC / eess.AS, date-windowed   (preprints live here)
  │    • S2 Recommendations API   seeded by DOIs already in README (≈1 req/s, backoff)
  │
  2. DEDUP / VERSION-MATCH (3-way)
  │    • exact DOI/arXiv-id already in README                        → SKIP
  │    • fuzzy title + first-author match an existing row (DOI differs)
  │         → UPDATE (published version of a listed preprint; also check
  │           Crossref relation is-preprint-of / has-preprint)
  │    • no match                                                    → NEW
  │    • drop anything already proposed in a prior open/closed scout PR (state file)
  │
  3. PREFILTER (free, no LLM)
  │    • embed title+abstract with all-MiniLM-L6-v2 (already used by the RAG backend)
  │    • cosine vs the centroid of the existing corpus embeddings; keep top-N / >threshold
  │    • hard rules: must mention a non-human primate term; drop pure-human / pure-cortex
  │
  4. JUDGE (free open-weight LLM, e.g. Groq Llama/Qwen)
  │    • score each survivor 0–1 against the rubric below
  │    • emit: keep/reject, justification (1 line), proposed topic tags, animal
  │
  5. ENRICH (fill the whole row — never emit "TBD")
  │    • Count  : regex images/frames/videos/clips over abstract + methods
  │    • Model? : scan OA landing page / PDF for github/gitlab/huggingface links
  │    • Data?  : scan for zenodo/figshare/dryad/HF/institutional, else "Upon request"
  │    • if the publisher page is gated (403/paywall) → fall back to OpenAlex
  │      best_oa_location (OA PDF) or the abstract. Honest negative is "N/A", not "TBD".
  │    • UPDATE case (journal version of a listed preprint) → inherit Model?/Data?/Count
  │      from the existing row; only the DOI changes.
  │    • low-confidence fields are flagged in the PR for human confirmation
  │
  6. DELIVER
       • open a DRAFT PR: new rows inserted in README in chronological order
       • PR body = table of kept papers (score + justification) AND rejected ones (for audit)
       • regenerate index.html in the same PR (so website.yml passes)
```

## The relevance rubric (the actual product)

A paper is **IN** only if it is a *novel deep-learning method, model, or dataset whose primary
subject is non-human primates* (or a cross-species animal dataset that meaningfully includes
primates). Concretely:

- ✅ new pose/detection/face/behavior/bioacoustic model or dataset for monkeys/apes/lemurs/etc.
- ✅ cross-species animal CV dataset that includes a primate split (e.g. AP-10K style)
- ❌ primate **visual cortex** modeled with a CNN (that's comp-neuro, not animal CV)
- ❌ generic CV/ML papers that merely mention primates or use "primate vision" as motivation
- ❌ human-only face/pose work
- ❌ pure field biology / ecology with no DL component
- ❌ reviews → route to the separate "Reviews & Related" list, not the main table

The judge returns `{decision, score, reason, animal, topic_tags}`; ENRICH then fills the row.
Borderline (0.4–0.7) papers are included in the PR but flagged "REVIEW" rather than auto-added.

## Entry lifecycle (a row is not write-once)

A listed paper changes state over time. The scout (and periodic audits) must handle:

| Event | Detection | Action |
|---|---|---|
| **Preprint → published** | title+author match; Crossref `is-preprint-of` | UPDATE link to version of record. **The link is canonical: year follows the link** (bump preprint year → publication year when the link is bumped). Inherit Model?/Data?/Count. |
| **Conf → journal extension** (genuinely expanded, not just VoR) | title near-match but content/length differs | flag for human: update-in-place *or* new row — editorial call, never auto. |
| **Retraction / withdrawal** | OpenAlex `is_retracted`; arXiv "withdrawn" | flag in PR for removal or `[RETRACTED]` annotation — don't recommend retracted work. |
| **Code/data released later** | re-scan existing `N/A` rows' pages for new repo/dataset links | propose upgrading `N/A → [Yes](url)`. Turns a stale row fresh. |
| **Link rot** (paper/code/data URL dies) | extend the weekly lychee check to code/data cells | propose downgrading the dead cell / swapping to an archive (Wayback, Zenodo). |
| **Dataset version/count drift** | re-read dataset page | low priority; refresh the count if materially changed. |
| **Re-proposal across weeks** | `scout-state.json` keyed by *work*, not DOI | a paper proposed as a preprint then later published is the **same work** — don't double-propose; convert the pending entry to an UPDATE. |

Going-forward, the scout handles these as they occur. For the existing list there's a one-time
**reconciliation sweep**: run the same matcher over every current entry to (a) find preprints
now published, (b) catch any `is_retracted`, (c) re-verify code/data links. One audit PR.

## Sources & APIs (verified May 2026)

| Source | Auth | Notes |
|---|---|---|
| OpenAlex | none (`mailto=`) | best default; per-day filtering, citation graph; very generous |
| arXiv | none | official API; where this field's preprints land first |
| Semantic Scholar Recommendations | free key | seed→similar; new keys throttled ~1 req/s, **exponential backoff required** |
| Crossref | none | DOI ↔ metadata normalization / join key |
| PubMed / Europe PMC | none | bioacoustics/neuro venues; PubMed MCP already available in-session |

Not usable: Google Scholar (no API, scrape-only), Consensus / Elicit (products, no public API).

> **Multi-source is mandatory, not optional.** Only ~26% of the current corpus (25/97) is on
> arXiv; the rest is bioRxiv (10.1101), Springer, IEEE, Nature, Elsevier, Wiley/AJP, PLOS, etc.
> A pure-arXiv bot would miss ~74% of the field. arXiv catches preprints early; OpenAlex +
> Crossref + PubMed catch the journal/biology venues where most primatology actually lands.

## Secrets / config (GitHub repo settings)

- `GROQ_API_KEY` — judge via a free open-weight model (Llama/Qwen/Gemma). Free tier
  (~1k req/day) dwarfs our weekly volume. `OPENROUTER_API_KEY` or `GEMINI_API_KEY` work as
  drop-in fallbacks (OpenAI-compatible).
- OpenAlex needs no key; pass `mailto=parodifelipe07@gmail.com` for the polite pool.
- `S2_API_KEY` — optional, only if we use the Recommendations API.
- Embeddings need **no key** — `all-MiniLM-L6-v2` runs on the CPU runner.
- `GITHUB_TOKEN` — auto-provided by Actions; used to open the draft PR.

Self-hosting a model in the runner is **not viable** (CPU-only, ~7 GB) — always call a hosted
free API. HuggingFace's own free `hf-inference` is fine for embeddings but the weakest option
for the LLM judge (CPU/embeddings-focused), so we use Groq/OpenRouter for that step.

## Proposed file layout

```
scripts/scout/
  __init__.py
  fetch.py        # OpenAlex + arXiv + S2 clients, date-windowed
  dedup.py        # README DOI/arXiv-id index + prior-PR state
  prefilter.py    # embeddings + hard rules (reuses sentence-transformers)
  judge.py        # Gemini call + rubric prompt (mirror backend/prompts.py style)
  propose.py      # build README rows + open draft PR (gh CLI / PyGithub)
  run.py          # orchestrator (mirrors scripts/rag/build_chunk_index.py)
.github/workflows/paper-scout.yml   # weekly cron + workflow_dispatch
docs/scout-state.json               # seen-ids, last-run window (committed by the bot)
```

## Failure modes & guardrails

- **API down / rate-limited** → backoff, skip that source, still ship a PR from the rest.
- **Zero candidates** → no PR (don't spam); log a one-line "nothing this week".
- **Judge over-permissive** → PR is draft + human-merge; rejected list is shown for calibration.
- **Cost** → prefilter caps how many papers reach the LLM; OpenAlex/arXiv are free.
- **Drift** → the rubric lives in version control; tweak it as the field's vocabulary shifts.

## Open questions for build session

1. Auto-add high-confidence (>0.8) rows vs. always leave PR fully manual? (Default: insert all
   kept rows, mark borderline as REVIEW; human merges.)
2. Include the 6-dataset and Reviews tables as nomination targets, or papers only?
3. Re-run the RAG embedding pipeline on newly-merged papers automatically? (ties into the
   existing TODO: 37 papers still need full-text download.)
4. Notification: comment-only PR, or also an email/Slack ping?
