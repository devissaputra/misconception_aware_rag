import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from misconception_aware_rag.core import (
    evaluate_case,
    generate_grounded_tutor_response,
    load_catalog_csv,
    load_documents_csv,
    retrieve_generic,
    retrieve_misconception_aware,
)


def split_pipe(value):
    return [
        item.strip()
        for item in value.split("|")
        if item.strip()
    ]


documents = load_documents_csv(ROOT / "data" / "documents.csv")
catalog = load_catalog_csv(ROOT / "data" / "misconceptions.csv")

cases = []
with (ROOT / "data" / "cases.csv").open(
    encoding="utf-8",
    newline="",
) as handle:
    for row in csv.DictReader(handle):
        row["expected_misconceptions"] = split_pipe(
            row["expected_misconceptions"]
        )
        row["relevant_document_ids"] = split_pipe(
            row["relevant_document_ids"]
        )
        cases.append(row)

print("Misconception-Aware RAG Tutor synthetic demo")
print()

detection_tp = detection_fp = detection_fn = 0
generic_recall = []
aware_recall = []
aware_mrr = []
abstentions = 0

for row in cases:
    plain_query = (
        row["task_question"] + " " + row["learner_response"]
    )
    generic = retrieve_generic(
        plain_query,
        documents,
        k=3,
    )
    generic_ids = [item["doc_id"] for item in generic]
    generic_hits = len(
        set(generic_ids)
        & set(row["relevant_document_ids"])
    )
    generic_recall.append(
        generic_hits / len(row["relevant_document_ids"])
        if row["relevant_document_ids"]
        else 1.0
    )

    aware = retrieve_misconception_aware(
        row["task_question"],
        row["learner_response"],
        documents,
        catalog,
        k=3,
    )
    result = evaluate_case(
        row["task_question"],
        row["learner_response"],
        documents,
        catalog,
        row["expected_misconceptions"],
        row["relevant_document_ids"],
        k=3,
    )
    aware_recall.append(
        result["retrieval_metrics"]["recall_at_k"]
    )
    aware_mrr.append(
        result["retrieval_metrics"]["reciprocal_rank"]
    )

    predicted = set(result["predicted_misconceptions"])
    expected = set(row["expected_misconceptions"])
    detection_tp += len(predicted & expected)
    detection_fp += len(predicted - expected)
    detection_fn += len(expected - predicted)

    response = generate_grounded_tutor_response(
        row["task_question"],
        row["learner_response"],
        aware,
        min_documents=2,
        min_top_score=0.5,
    )
    abstentions += response["status"] == "abstain"

    print(
        row["case_id"],
        {
            "type": row["case_type"],
            "expected": sorted(expected),
            "predicted": sorted(predicted),
            "generic_top3": generic_ids,
            "aware_top3": [
                item["doc_id"]
                for item in aware["results"]
            ],
            "response_status": response["status"],
            "citations": response["citations"],
        },
    )

precision = (
    detection_tp / (detection_tp + detection_fp)
    if detection_tp + detection_fp
    else 1.0
)
recall = (
    detection_tp / (detection_tp + detection_fn)
    if detection_tp + detection_fn
    else 1.0
)
f1 = (
    2 * precision * recall / (precision + recall)
    if precision + recall
    else 0.0
)

print("\nSynthetic component diagnostics:")
print(
    {
        "cases": len(cases),
        "misconception_precision": round(precision, 3),
        "misconception_recall": round(recall, 3),
        "misconception_f1": round(f1, 3),
        "generic_mean_recall_at_3": round(
            sum(generic_recall) / len(generic_recall),
            3,
        ),
        "aware_mean_recall_at_3": round(
            sum(aware_recall) / len(aware_recall),
            3,
        ),
        "aware_mean_reciprocal_rank": round(
            sum(aware_mrr) / len(aware_mrr),
            3,
        ),
        "abstentions": abstentions,
    }
)

focus = next(row for row in cases if row["case_id"] == "C01")
retrieval = retrieve_misconception_aware(
    focus["task_question"],
    focus["learner_response"],
    documents,
    catalog,
    k=3,
)
response = generate_grounded_tutor_response(
    focus["task_question"],
    focus["learner_response"],
    retrieval,
    min_documents=2,
    min_top_score=0.5,
)
print("\nGrounded response example:")
print(response["response"])

print(
    "\nNote: all documents, misconception labels, relevance judgments, "
    "authority values, and evaluation cases are synthetic. The deterministic "
    "generator proves the retrieval-to-citation software path; it is not an "
    "LLM and the synthetic metrics are not empirical results."
)
