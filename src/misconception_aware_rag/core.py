import math
import re
from collections import Counter


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def retrieve(query, documents, k=3):
    """Rank documents by normalized lexical overlap and drop zero overlap results."""
    if k <= 0:
        raise ValueError("k must be positive")
    query_counts = Counter(_tokens(query))
    if not query_counts:
        return []

    scored = []
    for doc_id, text in documents.items():
        document_counts = Counter(_tokens(text))
        overlap = sum(min(query_counts[token], document_counts[token]) for token in query_counts)
        if overlap == 0:
            continue
        norm = math.sqrt(sum(value * value for value in document_counts.values())) or 1.0
        scored.append((overlap / norm, doc_id, text))
    return sorted(scored, key=lambda row: (-row[0], str(row[1])))[:k]


def detect_misconception(answer, misconception_map):
    """Return labels whose configured cue appears in the learner answer."""
    lowered = answer.lower()
    return [
        label
        for label, cues in misconception_map.items()
        if any(cue.lower() in lowered for cue in cues)
    ]


def grounded_response(query, documents, misconception_map):
    """Return misconception flags and retrieved evidence without inventing an answer."""
    hits = detect_misconception(query, misconception_map)
    evidence = retrieve(query, documents, k=2)
    return {
        "misconceptions": hits,
        "evidence_ids": [row[1] for row in evidence],
        "evidence": [row[2] for row in evidence],
    }
