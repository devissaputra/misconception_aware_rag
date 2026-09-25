# Misconception-Aware RAG Tutor — Research Bundle

[![CI](https://github.com/devissaputra/misconception_aware_rag/actions/workflows/ci.yml/badge.svg)](https://github.com/devissaputra/misconception_aware_rag/actions/workflows/ci.yml)
[![Empirical Study](https://github.com/devissaputra/misconception_aware_rag/actions/workflows/empirical.yml/badge.svg)](https://github.com/devissaputra/misconception_aware_rag/actions/workflows/empirical.yml)

**Research Bundle · AI in Education · educational retrieval, wrong-answer conditioning, abstention and grounded tutoring**

![Misconception-Aware RAG Tutor architecture](assets/architecture.svg)

This repository contains two deliberately separated layers:

1. a transparent misconception-aware tutoring prototype with BM25 retrieval, cue-based hypothesis detection, pedagogical reranking, evidence sufficiency, abstention and deterministic citation-grounded generation;
2. a reproducible **real-data empirical study on SciQ** that evaluates whether conditioning retrieval on an observed wrong answer changes retrieval of the question's supporting evidence.

The empirical study does **not** claim that SciQ distractors are validated learner misconceptions.

## Empirical research question

> When retrieving science support passages, how does adding an observed wrong-answer option to the question change retrieval quality relative to a question-only BM25 baseline?

A third condition adds the gold correct answer. That condition is explicitly an **oracle upper bound**, not a deployable method.

## Real external dataset

The executable study uses the **SciQ** test split from the Allen Institute for AI / Hugging Face dataset repository.

- 13,679 questions in the full dataset;
- test split: 1,000 questions;
- fields include question, three distractors, correct answer and supporting paragraph;
- pinned dataset revision: `2c94ad3e1aafab77146f384e23536f97a4849815`;
- pinned test parquet SHA-256: `3a719356a29b127fc54ef3c7f51a034db4bd105d5717215e8c85d2aa58d60667`;
- license reported by the dataset card: CC BY-NC 3.0.

The source parquet is downloaded at run time and cached outside version control. See `DATA.md`.

## Frozen empirical conditions

For every SciQ test item with a non-empty support paragraph, the support paragraph is inserted into the retrieval corpus and its three distractors create three wrong-answer proxy cases.

The same BM25 index is evaluated under:

- **question_only** — question text only;
- **wrong_answer_conditioned** — question plus one incorrect answer option;
- **oracle_corrective** — question plus incorrect option plus the gold correct answer.

The primary comparison is wrong-answer-conditioned versus question-only. The oracle condition is sensitivity analysis only.

## Metrics and robustness

The study reports:

- mean reciprocal rank;
- Recall@1, Recall@3 and Recall@5;
- nDCG@5;
- question-block bootstrap interval for the paired MRR difference;
- counts of cases where wrong-answer conditioning improves, worsens or ties the baseline;
- per-case metrics without redistributing question/support text.

## Run the empirical study

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/run_sciq_study.py
```

Generated evidence:

- `results/metrics.json`
- `results/per_case_metrics.csv`
- `results/summary.md`
- `paper/results.md`

## Prototype pipeline

![Misconception-Aware RAG Tutor data flow](assets/data_flow.svg)

The prototype software remains available for research on a future validated misconception taxonomy:

```text
task question + learner response
        ↓
possible / rejected / ambiguous misconception hypothesis
        ↓
misconception-conditioned query expansion
        ↓
generic BM25 + pedagogical reranking
        ↓
evidence sufficiency
        ↓
citation-grounded response or abstention
```

The bundled CSV files under `data/` are intentionally small **synthetic software fixtures**. They exercise the prototype logic and are not the empirical evidence for this research bundle.

## Why the distinction matters

A distractor is an incorrect answer option. It may reflect a misconception, a plausible foil, a slip, incomplete knowledge, or simple test construction. The SciQ experiment therefore studies **wrong-answer-conditioned retrieval**, not diagnostic validity.

Likewise, the prototype's cue detector returns a *possible misconception* hypothesis. It must not be treated as a stable learner label.

## Interpretation boundary

This repository does not establish that:

- a SciQ distractor is a real learner misconception;
- lexical conditioning diagnoses why a learner answered incorrectly;
- retrieval improvement causes learning;
- citation presence guarantees semantic faithfulness;
- synthetic cue rules generalize to real tutoring dialogue;
- the oracle condition is deployable.

A future learner-facing study would require expert misconception annotation, held-out learner responses, privacy and consent review, pedagogical evaluation, and a clean separation between taxonomy construction and evaluation.

## Professor review path

`README.md` → `DATA.md` → `scripts/run_sciq_study.py` → `results/summary.md` → `results/metrics.json` → `RESEARCH_BUNDLE.md` → `REPRODUCIBILITY.md` → `ETHICS.md` → `paper/paper.md` → prototype core/tests.

## Citation

SciQ: Welbl, J., Liu, N. F., & Gardner, M. (2017). *Crowdsourcing Multiple Choice Science Questions*. arXiv:1707.06209.

Software citation is provided in `CITATION.cff`.
