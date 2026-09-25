# Misconception-Aware RAG Tutor — Empirical Research Bundle

[![CI](https://github.com/devissaputra/misconception_aware_rag/actions/workflows/ci.yml/badge.svg)](https://github.com/devissaputra/misconception_aware_rag/actions/workflows/ci.yml)
[![Empirical Study](https://github.com/devissaputra/misconception_aware_rag/actions/workflows/empirical.yml/badge.svg)](https://github.com/devissaputra/misconception_aware_rag/actions/workflows/empirical.yml)

**AI in Education · educational retrieval · wrong-answer conditioning · negative-control evaluation · reproducible research**

This repository intentionally separates two layers:

1. **Empirical research:** a frozen real-data SciQ study asking whether adding an observed wrong-answer option changes retrieval of the question's supporting evidence.
2. **Prototype software:** an inspectable misconception-aware tutoring pipeline using cue-based hypotheses, BM25, pedagogical reranking, evidence sufficiency, abstention and deterministic citation-grounded generation.

The empirical study does **not** validate the full tutoring prototype, and SciQ distractors are **not** treated as validated learner misconceptions.

## Research question

> Does conditioning a lexical evidence-retrieval query on an observed wrong answer change support-passage retrieval, and is any effect distinguishable from merely appending unrelated distractor-like text?

## Frozen external dataset

The executable study uses the SciQ test split from the Allen Institute for AI / Hugging Face dataset repository.

- full SciQ dataset: 13,679 questions;
- test split: 1,000 questions;
- pinned revision: `2c94ad3e1aafab77146f384e23536f97a4849815`;
- frozen test parquet SHA-256: `3a719356a29b127fc54ef3c7f51a034db4bd105d5717215e8c85d2aa58d60667`;
- license reported by the dataset card: CC BY-NC 3.0;
- original reference: Welbl, Liu & Gardner (2017), *Crowdsourcing Multiple Choice Science Questions*.

The empirical runner rejects source bytes that do not match the frozen hash.

## Four controlled retrieval conditions

The same BM25 corpus and retrieval settings are used throughout:

- **question_only** — the question alone;
- **wrong_answer_conditioned** — question + one actual SciQ distractor;
- **shuffled_wrong_answer_control** — question + distractor text from a different eligible question under a frozen no-self-match permutation;
- **oracle_corrective** — question + actual distractor + gold correct answer.

The shuffled condition is a **lexical-expansion negative control**. It preserves the marginal distractor-text distribution while deliberately breaking the question–answer relationship. This helps distinguish an effect of the observed wrong-answer content from a generic effect of adding distractor-like text.

The gold-answer condition is an **oracle-informed sensitivity condition**. It is not a mathematical upper bound and is not deployable.

## Frozen retrieval protocol

- BM25 `k1 = 1.5`, `b = 0.75`;
- retrieval depth `k = 5`;
- Unicode `\w+` tokenization after lowercasing;
- one support paragraph is the relevant document for each eligible question;
- all three distractors produce wrong-answer proxy cases;
- shuffled-control seed: `20260925`;
- primary question-block bootstrap seed: `20260925`;
- 3,000 bootstrap replicates;
- question, not distractor case, is the resampling unit.

The generated result manifest also records Python, pandas, pyarrow and platform versions.

## Metrics and robustness

The study reports MRR, Recall@1/3/5 and nDCG@5 for every condition, together with three paired question-block comparisons:

1. observed wrong answer vs question only;
2. shuffled wrong-answer control vs question only;
3. observed wrong answer vs shuffled wrong-answer control.

Directional improve/worsen/tie counts are also retained. Per-case files contain only identifiers, condition names, query-token counts and metrics—not SciQ question/support text.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
python -m unittest discover -s tests -v
python scripts/run_sciq_study.py
```

Generated evidence:

- `results/metrics.json`
- `results/per_case_metrics.csv`
- `results/summary.md`
- `paper/results.md`
- `paper/results.tex`

## Current empirical finding

Under the frozen SciQ/BM25 protocol:

- observed wrong-answer conditioning reduces MRR versus question-only retrieval by **0.0039** (95% question-block interval **[-0.0077, -0.0002]**);
- the shuffled lexical-expansion control also reduces MRR by **0.0024** (95% interval **[-0.0044, -0.0005]**);
- observed wrong-answer conditioning differs from the shuffled control by **-0.0014**, with interval **[-0.0057, 0.0027]**.

So the evidence does **not** show a clear content-specific benefit or penalty from the actual wrong answer beyond the generic cost of adding distractor-like lexical material. That negative result is the main empirical finding.

## Prototype boundary

The prototype can create possible/rejected/ambiguous misconception hypotheses, expand retrieval queries, rerank evidence, assess sufficiency and abstain or generate a deterministic citation-grounded response. Those components remain research scaffolding for a future learner-validated study.

The CSV files under `data/` are synthetic software fixtures only.

## Interpretation boundary

This repository does **not** establish that a SciQ distractor represents a learner misconception, that lexical query conditioning diagnoses learner reasoning, that retrieval relevance causes learning, that citations guarantee semantic faithfulness, or that the prototype is ready for consequential learner modeling.

## Professor review path

`README.md` → `DATA.md` → `scripts/run_sciq_study.py` → `results/summary.md` → `results/metrics.json` → `RESEARCH_BUNDLE.md` → `REPRODUCIBILITY.md` → `ETHICS.md` → `paper/paper.md` → `tests/test_sciq_study.py`.
