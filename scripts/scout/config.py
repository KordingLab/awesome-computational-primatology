#!/usr/bin/env python3
"""Configuration for the Paper Scout: queries, term lists, paths, thresholds."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
README_PATH = PROJECT_ROOT / "README.md"
CORPUS_PATH = PROJECT_ROOT / "data" / "papers_with_abstracts.json"
STATE_PATH = PROJECT_ROOT / "docs" / "scout-state.json"
WEBSITE_GENERATOR = PROJECT_ROOT / "scripts" / "website_generator.py"

# Polite-pool contact for the keyless OpenAlex/Crossref/arXiv APIs.
MAILTO = "parodifelipe07@gmail.com"

# Free open-weight LLM judge (Groq, OpenAI-compatible). Override via env.
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Score thresholds for the judge (0–1).
KEEP_THRESHOLD = 0.7      # >= → proposed as a ready row
REVIEW_THRESHOLD = 0.4    # [REVIEW, KEEP) → flagged for human review; < → rejected

# How far back to look when there is no prior state.
DEFAULT_LOOKBACK_DAYS = 14

# Focused (primate x method) OpenAlex searches, unioned for recall across venues.
OPENALEX_SEARCHES = [
    "primate pose estimation",
    "macaque behavior deep learning",
    "chimpanzee detection tracking video",
    "primate face recognition re-identification",
    "marmoset vocalization deep learning",
    "ape behavior recognition dataset",
    "lemur gibbon bioacoustics neural network",
]

# arXiv categories where this field's preprints land.
ARXIV_CATEGORIES = ["cs.CV", "q-bio.NC", "eess.AS", "cs.SD", "cs.LG"]

ANIMAL_TERMS = [
    "primate", "macaque", "rhesus", "monkey", "chimp", "chimpanzee", "ape",
    "gorilla", "marmoset", "lemur", "baboon", "bonobo", "gibbon", "orangutan",
    "loris", "langur", "capuchin", "tamarin", "mandrill", "vervet",
]
METHOD_TERMS = [
    "pose", "keypoint", "detection", "tracking", "recognition", "segmentation",
    "deep learning", "neural network", "cnn", "transformer", "behavior",
    "behaviour", "action", "classification", "face", "landmark",
    "re-identification", "reidentification", "vocalization", "vocalisation",
    "bioacoustic", "audio", "dataset", "benchmark", "computer vision", "video",
]
# Signals that usually mean "tangential" (primate-cortex-as-ML-model / human-only).
TANGENT_TERMS = [
    "visual cortex", "neural representation", "fmri", "human face",
    "patient", "object representation", "neuroai",
]

# Hosts that indicate code / dataset releases (used by enrich.py).
CODE_HOSTS = ["github.com", "gitlab.com", "huggingface.co", "codeberg.org", "bitbucket.org"]
DATA_HOSTS = ["zenodo.org", "figshare.com", "datadryad.org", "dryad", "osf.io",
              "data.mendeley.com", "huggingface.co/datasets"]
