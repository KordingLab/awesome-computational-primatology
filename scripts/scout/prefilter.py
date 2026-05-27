#!/usr/bin/env python3
"""Hard relevance rules + TF-IDF ranking against the curated corpus."""

from __future__ import annotations

import json

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import ANIMAL_TERMS, CORPUS_PATH, METHOD_TERMS, TANGENT_TERMS
from fetch import Candidate


def passes_rules(text: str) -> tuple[bool, bool]:
    """Apply hard relevance rules.

    Args:
        text: title + abstract.

    Returns:
        (keep, is_tangent): keep requires an animal term AND a method term;
        is_tangent flags likely primate-cortex / human-only papers.
    """
    low = text.lower()
    has_animal = any(t in low for t in ANIMAL_TERMS)
    has_method = any(t in low for t in METHOD_TERMS)
    is_tangent = any(t in low for t in TANGENT_TERMS)
    return (has_animal and has_method), is_tangent


def _corpus_texts() -> list[str]:
    """Return title+abstract strings for the existing curated corpus."""
    papers = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    texts = [f"{p.get('title', '')} {p.get('abstract', '')}".strip() for p in papers]
    return [t for t in texts if t]


def apply_rules(candidates: list[Candidate]) -> list[Candidate]:
    """Keep candidates passing the hard rules; set is_tangent on each survivor."""
    survivors = []
    for c in candidates:
        keep, tangent = passes_rules(c.text)
        if keep:
            c.is_tangent = tangent
            survivors.append(c)
    return survivors


def rank(candidates: list[Candidate]) -> list[Candidate]:
    """Score candidates by TF-IDF similarity to the corpus centroid, descending.

    Args:
        candidates: rule-passing candidates.

    Returns:
        The same candidates, with prefilter_score set, sorted high→low.
    """
    if not candidates:
        return []
    corpus = _corpus_texts()
    docs = corpus + [c.text for c in candidates]
    tfidf = TfidfVectorizer(stop_words="english", max_features=20000).fit_transform(docs)
    centroid = np.asarray(tfidf[: len(corpus)].mean(axis=0))
    scores = cosine_similarity(tfidf[len(corpus):], centroid).ravel()
    for c, s in zip(candidates, scores):
        c.prefilter_score = float(s)
    return sorted(candidates, key=lambda c: c.prefilter_score, reverse=True)


def prefilter(candidates: list[Candidate]) -> list[Candidate]:
    """Run rules then ranking."""
    return rank(apply_rules(candidates))
