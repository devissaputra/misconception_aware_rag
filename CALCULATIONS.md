# Calculation guide

## Question and evidence

Does adding a wrong answer improve evidence retrieval?

SciQ: 884 supported questions, 884 support documents and 2,652 distractor cases.

**Status:** RECORDED EXTERNAL-DATA STUDY | full experiment not rerun in this review.

## Design

BM25 question-only retrieval versus observed distractor, shuffled distractor and gold-answer oracle conditions.

## Calculation and interpretation

`Reciprocal rank = 1/rank of the relevant support; MRR = mean reciprocal rank.`

Three distractor cases share each question, so uncertainty resamples question blocks. Distractors are proxies, not validated learner misconceptions. Gold-answer expansion has privileged information and is not a deployable method.

## Evidence table

Selected recorded values (units and context shown). Full precision below is for traceability, not a claim of measurement precision.

| Quantity | Value | Unit / meaning | JSON path |
|---|---:|---|---|
| question_only | 0.9471530920060329 | MRR ↑ | `metrics.question_only.rr` |
| wrong_answer_conditioned | 0.9432629462041229 | MRR ↑ | `metrics.wrong_answer_conditioned.rr` |
| shuffled_wrong_answer_control | 0.9447083961789843 | MRR ↑ | `metrics.shuffled_wrong_answer_control.rr` |
| oracle_corrective | 0.9612242332830566 | MRR ↑ | `metrics.oracle_corrective.rr` |

Source: [results/metrics.json](results/metrics.json). Values resolve directly from this file when figures are regenerated.

Wrong-answer expansion slightly reduces MRR from 0.9472 to 0.9433 in the frozen benchmark. Its contrast with a shuffled distractor control has an interval spanning zero, so the study does not establish a distinct benefit from the semantic relationship of the wrong answer. The repository therefore separates the measured retrieval result from the tutoring prototype and makes no claim of improved learning.

## Verification performed in this review

The existing suite requires unavailable dependencies; no full-suite pass is claimed. The bundled demonstration executed successfully in this review. Stored empirical results were inspected, not independently reproduced from raw data.

The figure-generation check verifies agreement between the selected source values and SVGs. It does not validate the raw dataset, fitted model, identification assumptions, or external generalization.

```bash
python scripts/build_review_figures.py
python scripts/build_review_figures.py --check
```

## Implementation map

Follow these functions to inspect each transformation. Validation helpers and private functions remain visible in the linked modules.

| Function | Purpose / documented behavior |
|---|---|
| [`split_pipe`](scripts/run_demo.py#L18) | Inspect the explicit implementation and its callers. |
| [`tokens`](scripts/run_sciq_study.py#L42) | Inspect the explicit implementation and its callers. |
| [`validate_source_hash`](scripts/run_sciq_study.py#L46) | Inspect the explicit implementation and its callers. |
| [`reciprocal_rank`](scripts/run_sciq_study.py#L105) | Inspect the explicit implementation and its callers. |
| [`recall_at`](scripts/run_sciq_study.py#L112) | Inspect the explicit implementation and its callers. |
| [`ndcg_at`](scripts/run_sciq_study.py#L116) | Inspect the explicit implementation and its callers. |
| [`download_test`](scripts/run_sciq_study.py#L124) | Inspect the explicit implementation and its callers. |
| [`build_study`](scripts/run_sciq_study.py#L159) | Inspect the explicit implementation and its callers. |
| [`shuffled_wrong_answer_lookup`](scripts/run_sciq_study.py#L190) | Map each case to distractor text from a different question. |
| [`evaluate`](scripts/run_sciq_study.py#L211) | Inspect the explicit implementation and its callers. |
| [`aggregate`](scripts/run_sciq_study.py#L252) | Inspect the explicit implementation and its callers. |
| [`aggregate_query_lengths`](scripts/run_sciq_study.py#L263) | Inspect the explicit implementation and its callers. |
| [`question_block_bootstrap`](scripts/run_sciq_study.py#L270) | Inspect the explicit implementation and its callers. |
| [`directional_analysis`](scripts/run_sciq_study.py#L305) | Inspect the explicit implementation and its callers. |
| [`build_results_latex`](scripts/run_sciq_study.py#L329) | Inspect the explicit implementation and its callers. |
| [`write_outputs`](scripts/run_sciq_study.py#L408) | Inspect the explicit implementation and its callers. |
| [`run_study`](scripts/run_sciq_study.py#L592) | Inspect the explicit implementation and its callers. |
| [`main`](scripts/run_sciq_study.py#L643) | Inspect the explicit implementation and its callers. |
| [`rank`](scripts/run_sciq_study.py#L85) | Inspect the explicit implementation and its callers. |
| [`detect_misconceptions`](src/misconception_aware_rag/core.py#L162) | Return cue-level misconception candidates with rejection handling. |
| [`build_retrieval_query`](src/misconception_aware_rag/core.py#L232) | Condition retrieval on possible misconception concepts. |
| [`retrieve_generic`](src/misconception_aware_rag/core.py#L324) | Transparent BM25 retrieval baseline without misconception boosts. |
| [`retrieve_misconception_aware`](src/misconception_aware_rag/core.py#L368) | BM25 retrieval conditioned on possible misconception evidence. |
| [`assess_evidence_sufficiency`](src/misconception_aware_rag/core.py#L519) | Return transparent sufficiency/abstention diagnostics. |
| [`generate_grounded_tutor_response`](src/misconception_aware_rag/core.py#L578) | Deterministic citation-grounded response baseline; not an LLM. |
| [`precision_recall_f1`](src/misconception_aware_rag/core.py#L670) | Inspect the explicit implementation and its callers. |
| [`retrieval_metrics`](src/misconception_aware_rag/core.py#L696) | Inspect the explicit implementation and its callers. |
| [`evaluate_case`](src/misconception_aware_rag/core.py#L742) | Inspect the explicit implementation and its callers. |
| [`load_documents_csv`](src/misconception_aware_rag/core.py#L791) | Inspect the explicit implementation and its callers. |
| [`load_catalog_csv`](src/misconception_aware_rag/core.py#L814) | Inspect the explicit implementation and its callers. |
| [`retrieve`](src/misconception_aware_rag/core.py#L843) | Inspect the explicit implementation and its callers. |
| [`detect_misconception`](src/misconception_aware_rag/core.py#L867) | Inspect the explicit implementation and its callers. |
| [`grounded_response`](src/misconception_aware_rag/core.py#L889) | Inspect the explicit implementation and its callers. |

## What remains before a stronger research claim

Three distractor cases share each question, so uncertainty resamples question blocks. Distractors are proxies, not validated learner misconceptions. Gold-answer expansion has privileged information and is not a deployable method. A successful software test is not validation of a scientific construct. New experiments should state their split unit, comparator, outcome, uncertainty procedure and failure criteria before examining final test results.
