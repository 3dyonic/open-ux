"""In-process BM25 over static catalog JSON. No daemon, no embeddings, no HyDE."""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Sequence
from typing import Any

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_STOP = frozenset(
    {
        "a",
        "an",
        "the",
        "to",
        "for",
        "of",
        "and",
        "or",
        "in",
        "on",
        "this",
        "that",
        "these",
        "those",
        "is",
        "are",
        "be",
        "with",
        "from",
        "as",
        "at",
        "vs",
        "it",
        "its",
        "into",
        "am",
        "i",
        "me",
        "my",
        "we",
        "our",
        "you",
        "your",
        "they",
        "their",
        "them",
        "can",
        "could",
        "should",
        "would",
    }
)
_K1 = 1.2
_B = 0.75
_PHRASE_BONUS = 100.0


def tokens(text: str) -> list[str]:
    return [
        token
        for token in _TOKEN_RE.findall(text.lower())
        if token not in _STOP and len(token) > 1
    ]


def guideline_blob(guideline: dict[str, Any]) -> str:
    return " ".join(
        [
            str(guideline.get("id") or ""),
            str(guideline.get("title") or ""),
            str(guideline.get("name") or ""),
            str(guideline.get("rule") or ""),
            " ".join(guideline.get("pass_when") or []),
            " ".join(guideline.get("fail_when") or []),
            str(guideline.get("facet") or ""),
        ]
    )


def _idf(df: int, n_docs: int) -> float:
    return math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))


def blob_scores(query: str, blobs: Sequence[str]) -> list[float]:
    """BM25 + phrase bonus per blob, input order."""
    q = (query or "").strip()
    if not q or not blobs:
        return [0.0] * len(blobs)
    q_tokens = tokens(q)
    needle = q.lower()
    docs = [tokens(blob) for blob in blobs]
    n_docs = len(docs)
    df: Counter[str] = Counter()
    for doc in docs:
        df.update(set(doc))
    lengths = [len(doc) or 1 for doc in docs]
    avgdl = sum(lengths) / n_docs
    scores = [0.0] * n_docs
    for index, (doc, blob, dl) in enumerate(zip(docs, blobs, lengths)):
        tf = Counter(doc)
        score = 0.0
        for term in q_tokens:
            if term not in tf:
                continue
            freq = tf[term]
            denom = freq + _K1 * (1.0 - _B + _B * dl / avgdl)
            score += _idf(df[term], n_docs) * (freq * (_K1 + 1.0)) / denom
        if needle in blob.lower():
            score += _PHRASE_BONUS
        scores[index] = score
    return scores


def rank_blobs(query: str, blobs: Sequence[str]) -> tuple[list[int], bool]:
    """Return indices ordered by BM25 (then original index). matched if any score > 0.

    Phrase hits get a bonus so a full-query substring still leads token-only
    hits (OUX-24). Zero hits keep the input order (fail-open).
    """
    scores = blob_scores(query, blobs)
    n_docs = len(blobs)
    if not scores or not any(value > 0 for value in scores):
        return list(range(n_docs)), False
    order = sorted(range(n_docs), key=lambda i: (-scores[i], i))
    return order, True
