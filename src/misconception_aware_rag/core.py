# Calculation reading guide: ../CALCULATIONS.md (repository root).
# Reciprocal rank = 1/rank of the relevant support; MRR = mean reciprocal rank.
# Three distractor cases share each question, so uncertainty resamples question blocks. Distractors are proxies, not validated learner misconceptions. Gold-answer expansion has privileged information and is not a deployable method.

import csv
import math
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


EVIDENCE_KINDS = {
    "explanation",
    "counterevidence",
    "worked_example",
    "remediation",
    "definition",
}

DETECTION_STATUSES = {
    "possible",
    "rejected",
    "ambiguous",
}


def _text(value, name, *, optional=False):
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        if optional:
            raise ValueError(
                f"{name} must be a non-empty string or None"
            )
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _positive_int(value, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _unit_interval(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and between 0 and 1")
    return value


def _tokens(text):
    if not text:
        return []
    return re.findall(
        r"[^\W_]+(?:['’-][^\W_]+)?",
        text.lower(),
        flags=re.UNICODE,
    )


def _phrase_present(text, phrase):
    text_tokens = _tokens(text)
    phrase_tokens = _tokens(phrase)
    if not phrase_tokens:
        return False
    width = len(phrase_tokens)
    return any(
        text_tokens[index:index + width] == phrase_tokens
        for index in range(len(text_tokens) - width + 1)
    )


def _split_pipe(value):
    if value in (None, ""):
        return ()
    return tuple(
        part.strip()
        for part in value.split("|")
        if part.strip()
    )


@dataclass(frozen=True)
class EvidenceDocument:
    doc_id: str
    concept: str
    kind: str
    text: str
    source: str = "synthetic_course"
    authority: float = 1.0

    def __post_init__(self):
        object.__setattr__(self, "doc_id", _text(self.doc_id, "doc_id"))
        object.__setattr__(self, "concept", _text(self.concept, "concept"))
        object.__setattr__(self, "kind", _text(self.kind, "kind"))
        object.__setattr__(self, "text", _text(self.text, "text"))
        object.__setattr__(self, "source", _text(self.source, "source"))
        if self.kind not in EVIDENCE_KINDS:
            raise ValueError(
                f"kind must be one of {sorted(EVIDENCE_KINDS)}"
            )
        object.__setattr__(
            self,
            "authority",
            _unit_interval(self.authority, "authority"),
        )


@dataclass(frozen=True)
class MisconceptionRecord:
    misconception_id: str
    concept: str
    canonical_statement: str
    description: str
    positive_cues: tuple[str, ...]
    negative_cues: tuple[str, ...] = ()
    corrective_concepts: tuple[str, ...] = ()
    remediation: str | None = None
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self):
        object.__setattr__(
            self,
            "misconception_id",
            _text(self.misconception_id, "misconception_id"),
        )
        object.__setattr__(self, "concept", _text(self.concept, "concept"))
        object.__setattr__(
            self,
            "canonical_statement",
            _text(self.canonical_statement, "canonical_statement"),
        )
        object.__setattr__(
            self,
            "description",
            _text(self.description, "description"),
        )
        if not isinstance(self.positive_cues, tuple) or not self.positive_cues:
            raise ValueError("positive_cues must be a non-empty tuple")
        for cue in self.positive_cues:
            _text(cue, "positive cue")
        for cue in self.negative_cues:
            _text(cue, "negative cue")
        for concept in self.corrective_concepts:
            _text(concept, "corrective concept")
        for doc_id in self.evidence_ids:
            _text(doc_id, "evidence id")
        object.__setattr__(
            self,
            "remediation",
            _text(self.remediation, "remediation", optional=True),
        )


def detect_misconceptions(learner_response, catalog):
    """Return cue-level misconception candidates with rejection handling."""
    learner_response = _text(
        learner_response,
        "learner_response",
    )
    if not isinstance(catalog, Sequence) or isinstance(
        catalog,
        (str, bytes),
    ):
        raise ValueError("catalog must be a sequence")
    if not all(
        isinstance(record, MisconceptionRecord)
        for record in catalog
    ):
        raise ValueError(
            "catalog must contain MisconceptionRecord objects"
        )

    detections = []
    for record in catalog:
        positive = [
            cue
            for cue in record.positive_cues
            if _phrase_present(learner_response, cue)
        ]
        negative = [
            cue
            for cue in record.negative_cues
            if _phrase_present(learner_response, cue)
        ]
        if not positive and not negative:
            continue

        if positive and negative:
            status = "ambiguous"
        elif negative:
            status = "rejected"
        else:
            status = "possible"

        cue_total = len(record.positive_cues) + len(record.negative_cues)
        cue_hits = len(positive) + len(negative)
        score = min(1.0, 0.55 + 0.45 * cue_hits / max(1, cue_total))

        detections.append(
            {
                "misconception_id": record.misconception_id,
                "concept": record.concept,
                "canonical_statement": record.canonical_statement,
                "status": status,
                "cue_score": round(score, 6),
                "matched_positive_cues": positive,
                "matched_negative_cues": negative,
                "corrective_concepts": list(record.corrective_concepts),
                "remediation": record.remediation,
                "evidence_ids": list(record.evidence_ids),
            }
        )

    detections.sort(
        key=lambda row: (
            {"possible": 0, "ambiguous": 1, "rejected": 2}[row["status"]],
            -row["cue_score"],
            row["misconception_id"],
        )
    )
    return detections


def build_retrieval_query(
    task_question,
    learner_response,
    detections,
):
    """Condition retrieval on possible misconception concepts."""
    task_question = _text(
        task_question,
        "task_question",
        optional=True,
    )
    learner_response = _text(
        learner_response,
        "learner_response",
    )
    if not isinstance(detections, Sequence):
        raise ValueError("detections must be a sequence")

    parts = []
    if task_question:
        parts.append(task_question)
    parts.append(learner_response)

    expansions = []
    for row in detections:
        if row.get("status") != "possible":
            continue
        concept = row.get("concept")
        if concept:
            expansions.append(concept)
        expansions.extend(row.get("corrective_concepts", []))

    seen = set()
    for expansion in expansions:
        normalized = expansion.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            parts.append(expansion)

    return " ".join(parts)


def _bm25_scores(query, documents, *, k1=1.5, b=0.75):
    if not documents:
        return {}
    query_tokens = _tokens(query)
    if not query_tokens:
        return {document.doc_id: 0.0 for document in documents}

    tokenized = {
        document.doc_id: _tokens(document.text)
        for document in documents
    }
    lengths = {
        doc_id: len(tokens)
        for doc_id, tokens in tokenized.items()
    }
    average_length = sum(lengths.values()) / max(1, len(lengths))

    document_frequency = Counter()
    for tokens in tokenized.values():
        for token in set(tokens):
            document_frequency[token] += 1

    query_counts = Counter(query_tokens)
    n_docs = len(documents)
    scores = {}
    for document in documents:
        tokens = tokenized[document.doc_id]
        counts = Counter(tokens)
        length = max(1, lengths[document.doc_id])
        score = 0.0
        for token, query_count in query_counts.items():
            tf = counts.get(token, 0)
            if tf == 0:
                continue
            df = document_frequency[token]
            idf = math.log(
                1.0 + (n_docs - df + 0.5) / (df + 0.5)
            )
            denominator = tf + k1 * (
                1.0 - b + b * length / max(1.0, average_length)
            )
            score += (
                idf
                * (tf * (k1 + 1.0) / denominator)
                * min(query_count, 2)
            )
        scores[document.doc_id] = score
    return scores


def retrieve_generic(query, documents, k=5):
    """Transparent BM25 retrieval baseline without misconception boosts."""
    query = _text(query, "query")
    k = _positive_int(k, "k")
    if not isinstance(documents, Sequence) or isinstance(
        documents,
        (str, bytes),
    ):
        raise ValueError("documents must be a sequence")
    if not all(
        isinstance(document, EvidenceDocument)
        for document in documents
    ):
        raise ValueError(
            "documents must contain EvidenceDocument objects"
        )
    ids = [document.doc_id for document in documents]
    if len(ids) != len(set(ids)):
        raise ValueError("document ids must be unique")

    scores = _bm25_scores(query, documents)
    ranked = [
        {
            "doc_id": document.doc_id,
            "concept": document.concept,
            "kind": document.kind,
            "text": document.text,
            "source": document.source,
            "authority": document.authority,
            "bm25_score": scores[document.doc_id],
            "misconception_boost": 0.0,
            "kind_boost": 0.0,
            "authority_boost": 0.0,
            "final_score": scores[document.doc_id],
        }
        for document in documents
        if scores[document.doc_id] > 0
    ]
    ranked.sort(
        key=lambda row: (-row["final_score"], row["doc_id"])
    )
    return ranked[:k]


def retrieve_misconception_aware(
    task_question,
    learner_response,
    documents,
    catalog,
    *,
    k=5,
):
    """BM25 retrieval conditioned on possible misconception evidence."""
    k = _positive_int(k, "k")
    detections = detect_misconceptions(
        learner_response,
        catalog,
    )
    query = build_retrieval_query(
        task_question,
        learner_response,
        detections,
    )

    generic = retrieve_generic(
        query,
        documents,
        k=max(k, len(documents)),
    )
    by_id = {document.doc_id: document for document in documents}

    active = [
        row
        for row in detections
        if row["status"] == "possible"
    ]
    active_concepts = {
        row["concept"].lower()
        for row in active
    }
    corrective_concepts = {
        concept.lower()
        for row in active
        for concept in row["corrective_concepts"]
    }
    preferred_ids = {
        doc_id
        for row in active
        for doc_id in row["evidence_ids"]
    }

    kind_weights = {
        "counterevidence": 0.45,
        "remediation": 0.35,
        "worked_example": 0.30,
        "explanation": 0.20,
        "definition": 0.10,
    }

    ranked = []
    for row in generic:
        document = by_id[row["doc_id"]]
        concept = document.concept.lower()

        misconception_boost = 0.0
        if document.doc_id in preferred_ids:
            misconception_boost += 0.85
        if concept in active_concepts:
            misconception_boost += 0.40
        if concept in corrective_concepts:
            misconception_boost += 0.55

        kind_boost = (
            kind_weights.get(document.kind, 0.0)
            if active
            else 0.0
        )
        authority_boost = 0.15 * document.authority
        final_score = (
            row["bm25_score"]
            + misconception_boost
            + kind_boost
            + authority_boost
        )

        updated = dict(row)
        updated.update(
            {
                "misconception_boost": round(
                    misconception_boost,
                    6,
                ),
                "kind_boost": round(kind_boost, 6),
                "authority_boost": round(
                    authority_boost,
                    6,
                ),
                "final_score": round(final_score, 6),
            }
        )
        ranked.append(updated)

    # Preferred misconception evidence may have zero lexical overlap with
    # the learner's incorrect wording. Add it explicitly with a transparent
    # metadata score rather than silently dropping it.
    retrieved_ids = {row["doc_id"] for row in ranked}
    for doc_id in sorted(preferred_ids - retrieved_ids):
        if doc_id not in by_id:
            continue
        document = by_id[doc_id]
        concept = document.concept.lower()
        misconception_boost = 0.85
        if concept in active_concepts:
            misconception_boost += 0.40
        if concept in corrective_concepts:
            misconception_boost += 0.55
        kind_boost = kind_weights.get(document.kind, 0.0)
        authority_boost = 0.15 * document.authority
        ranked.append(
            {
                "doc_id": document.doc_id,
                "concept": document.concept,
                "kind": document.kind,
                "text": document.text,
                "source": document.source,
                "authority": document.authority,
                "bm25_score": 0.0,
                "misconception_boost": round(
                    misconception_boost,
                    6,
                ),
                "kind_boost": round(kind_boost, 6),
                "authority_boost": round(
                    authority_boost,
                    6,
                ),
                "final_score": round(
                    misconception_boost
                    + kind_boost
                    + authority_boost,
                    6,
                ),
            }
        )

    ranked.sort(
        key=lambda row: (-row["final_score"], row["doc_id"])
    )
    return {
        "detections": detections,
        "retrieval_query": query,
        "results": ranked[:k],
    }


def assess_evidence_sufficiency(
    retrieval_result,
    *,
    min_documents=2,
    min_top_score=0.5,
):
    """Return transparent sufficiency/abstention diagnostics."""
    min_documents = _positive_int(
        min_documents,
        "min_documents",
    )
    if isinstance(min_top_score, bool) or not isinstance(
        min_top_score,
        (int, float),
    ):
        raise ValueError("min_top_score must be numeric")
    min_top_score = float(min_top_score)
    if not math.isfinite(min_top_score) or min_top_score < 0:
        raise ValueError(
            "min_top_score must be finite and non-negative"
        )
    if not isinstance(retrieval_result, Mapping):
        raise ValueError(
            "retrieval_result must be a mapping"
        )

    results = retrieval_result.get("results", [])
    active = [
        row
        for row in retrieval_result.get("detections", [])
        if row.get("status") == "possible"
    ]
    reasons = []

    if len(results) < min_documents:
        reasons.append("too_few_evidence_passages")
    top_score = results[0]["final_score"] if results else 0.0
    if top_score < min_top_score:
        reasons.append("top_evidence_score_below_threshold")

    if active:
        kinds = {row["kind"] for row in results}
        if not (
            "counterevidence" in kinds
            or "explanation" in kinds
        ):
            reasons.append(
                "missing_explanatory_or_counterevidence_passage"
            )

    return {
        "sufficient": not reasons,
        "reasons": reasons,
        "evidence_count": len(results),
        "top_score": round(top_score, 6),
        "possible_misconception_count": len(active),
    }


def generate_grounded_tutor_response(
    task_question,
    learner_response,
    retrieval_result,
    *,
    min_documents=2,
    min_top_score=0.5,
):
    """Deterministic citation-grounded response baseline; not an LLM."""
    _text(task_question, "task_question", optional=True)
    _text(learner_response, "learner_response")
    sufficiency = assess_evidence_sufficiency(
        retrieval_result,
        min_documents=min_documents,
        min_top_score=min_top_score,
    )
    results = retrieval_result.get("results", [])
    possible = [
        row
        for row in retrieval_result.get("detections", [])
        if row.get("status") == "possible"
    ]
    ambiguous = [
        row
        for row in retrieval_result.get("detections", [])
        if row.get("status") == "ambiguous"
    ]

    if not sufficiency["sufficient"]:
        citations = [row["doc_id"] for row in results]
        return {
            "status": "abstain",
            "response": (
                "I do not have enough course evidence to make a reliable "
                "misconception-specific correction yet."
            ),
            "citations": citations,
            "diagnosis": [],
            "evidence_sufficiency": sufficiency,
            "generator": "deterministic_template",
        }

    citations = [row["doc_id"] for row in results]
    evidence_sentences = " ".join(
        f"[{row['doc_id']}] {row['text']}"
        for row in results[:3]
    )

    if possible:
        labels = [
            row["canonical_statement"]
            for row in possible[:2]
        ]
        diagnosis_text = (
            "A possible misconception is: "
            + "; ".join(labels)
            + ". "
        )
        diagnosis = [
            row["misconception_id"]
            for row in possible[:2]
        ]
    elif ambiguous:
        diagnosis_text = (
            "Your response contains language associated with a known "
            "misconception, but the evidence is ambiguous. "
        )
        diagnosis = []
    else:
        diagnosis_text = (
            "I did not detect a configured misconception cue. "
        )
        diagnosis = []

    response = (
        diagnosis_text
        + "Relevant course evidence: "
        + evidence_sentences
        + " Check your reasoning against these cited passages and revise "
        + "only if the evidence supports a change."
    )

    return {
        "status": "grounded_response",
        "response": response,
        "citations": citations[:3],
        "diagnosis": diagnosis,
        "evidence_sufficiency": sufficiency,
        "generator": "deterministic_template",
    }


def precision_recall_f1(predicted, expected):
    predicted = set(predicted)
    expected = set(expected)
    true_positive = len(predicted & expected)
    precision = (
        true_positive / len(predicted)
        if predicted
        else (1.0 if not expected else 0.0)
    )
    recall = (
        true_positive / len(expected)
        if expected
        else 1.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def retrieval_metrics(ranked_ids, relevant_ids, *, k=None):
    if not isinstance(ranked_ids, Sequence) or isinstance(
        ranked_ids,
        (str, bytes),
    ):
        raise ValueError("ranked_ids must be a sequence")
    relevant = set(relevant_ids)
    if k is None:
        k = len(ranked_ids)
    else:
        k = _positive_int(k, "k")
    selected = list(ranked_ids[:k])

    hits = [doc_id for doc_id in selected if doc_id in relevant]
    precision_at_k = len(hits) / k
    recall_at_k = (
        len(set(hits)) / len(relevant)
        if relevant
        else 1.0
    )

    reciprocal_rank = 0.0
    for index, doc_id in enumerate(selected, start=1):
        if doc_id in relevant:
            reciprocal_rank = 1.0 / index
            break

    dcg = 0.0
    for index, doc_id in enumerate(selected, start=1):
        if doc_id in relevant:
            dcg += 1.0 / math.log2(index + 1)
    ideal_hits = min(len(relevant), k)
    idcg = sum(
        1.0 / math.log2(index + 1)
        for index in range(1, ideal_hits + 1)
    )
    ndcg = dcg / idcg if idcg else 1.0

    return {
        "precision_at_k": precision_at_k,
        "recall_at_k": recall_at_k,
        "reciprocal_rank": reciprocal_rank,
        "ndcg_at_k": ndcg,
    }


def evaluate_case(
    task_question,
    learner_response,
    documents,
    catalog,
    expected_misconceptions,
    relevant_document_ids,
    *,
    k=5,
):
    retrieval = retrieve_misconception_aware(
        task_question,
        learner_response,
        documents,
        catalog,
        k=k,
    )
    predicted = [
        row["misconception_id"]
        for row in retrieval["detections"]
        if row["status"] == "possible"
    ]
    detection_metrics = precision_recall_f1(
        predicted,
        expected_misconceptions,
    )
    ranked_ids = [
        row["doc_id"]
        for row in retrieval["results"]
    ]
    ranking_metrics = retrieval_metrics(
        ranked_ids,
        relevant_document_ids,
        k=k,
    )
    response = generate_grounded_tutor_response(
        task_question,
        learner_response,
        retrieval,
    )
    return {
        "predicted_misconceptions": predicted,
        "detection_metrics": detection_metrics,
        "retrieval_metrics": ranking_metrics,
        "response_status": response["status"],
        "citations": response["citations"],
    }


def load_documents_csv(path):
    documents = []
    with Path(path).open(
        encoding="utf-8",
        newline="",
    ) as handle:
        for row in csv.DictReader(handle):
            documents.append(
                EvidenceDocument(
                    doc_id=row.get("doc_id"),
                    concept=row.get("concept"),
                    kind=row.get("kind"),
                    text=row.get("text"),
                    source=row.get("source") or "synthetic_course",
                    authority=float(row.get("authority") or 1.0),
                )
            )
    ids = [document.doc_id for document in documents]
    if len(ids) != len(set(ids)):
        raise ValueError("document ids must be unique")
    return documents


def load_catalog_csv(path):
    records = []
    with Path(path).open(
        encoding="utf-8",
        newline="",
    ) as handle:
        for row in csv.DictReader(handle):
            records.append(
                MisconceptionRecord(
                    misconception_id=row.get("misconception_id"),
                    concept=row.get("concept"),
                    canonical_statement=row.get("canonical_statement"),
                    description=row.get("description"),
                    positive_cues=_split_pipe(row.get("positive_cues")),
                    negative_cues=_split_pipe(row.get("negative_cues")),
                    corrective_concepts=_split_pipe(
                        row.get("corrective_concepts")
                    ),
                    remediation=row.get("remediation") or None,
                    evidence_ids=_split_pipe(row.get("evidence_ids")),
                )
            )
    ids = [record.misconception_id for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("misconception ids must be unique")
    return records


# Backward-compatible wrappers from the original prototype.
def retrieve(query, documents, k=3):
    if not isinstance(documents, Mapping):
        raise ValueError(
            "legacy retrieve expects a mapping of doc_id to text"
        )
    wrapped = [
        EvidenceDocument(
            doc_id=str(doc_id),
            concept="legacy",
            kind="explanation",
            text=text,
        )
        for doc_id, text in documents.items()
    ]
    return [
        (
            row["final_score"],
            row["doc_id"],
            row["text"],
        )
        for row in retrieve_generic(query, wrapped, k=k)
    ]


def detect_misconception(answer, misconception_map):
    if not isinstance(misconception_map, Mapping):
        raise ValueError(
            "legacy misconception_map must be a mapping"
        )
    catalog = [
        MisconceptionRecord(
            misconception_id=str(label),
            concept=str(label),
            canonical_statement=str(label),
            description="Legacy cue-matching record",
            positive_cues=tuple(cues),
        )
        for label, cues in misconception_map.items()
    ]
    return [
        row["misconception_id"]
        for row in detect_misconceptions(answer, catalog)
        if row["status"] == "possible"
    ]


def grounded_response(query, documents, misconception_map):
    hits = detect_misconception(query, misconception_map)
    evidence = retrieve(query, documents, k=2)
    return {
        "misconceptions": hits,
        "evidence_ids": [row[1] for row in evidence],
        "evidence": [row[2] for row in evidence],
    }
