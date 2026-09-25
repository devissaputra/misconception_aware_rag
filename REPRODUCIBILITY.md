# Reproducibility Protocol

## Install and test

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
python -m unittest discover -s tests -v
python scripts/run_demo.py
```

## Real-data empirical run

```bash
python scripts/run_sciq_study.py
```

## Frozen source

- SciQ revision: `2c94ad3e1aafab77146f384e23536f97a4849815`
- test parquet SHA-256: `3a719356a29b127fc54ef3c7f51a034db4bd105d5717215e8c85d2aa58d60667`
- expected test rows: 1,000

## Frozen retrieval parameters

- BM25 `k1 = 1.5`
- BM25 `b = 0.75`
- retrieval depth `k = 5`
- Unicode `\w+` tokenization after lowercasing
- shuffled-control seed `20260925`
- primary bootstrap seed `20260925`
- default bootstrap replicates `3000`

## Dependence and controls

Each eligible question contributes three distractor cases. Bootstrap resampling therefore occurs by **question block**, not by distractor case.

The shuffled wrong-answer condition uses distractor text from other questions under a frozen derangement. It preserves the marginal distractor-text distribution and provides a lexical-expansion negative control.

## Generated evidence

- `results/metrics.json`
- `results/per_case_metrics.csv`
- `results/summary.md`
- `paper/results.md`
- `paper/results.tex`

The result manifest records protocol constants and Python/pandas/pyarrow/platform versions.

## Evidence-integrity CI

`tests/test_sciq_study.py` verifies the frozen hash guard, support-document construction, shuffled-control no-self-match property, question-level bootstrap behavior, absence of raw text in per-case output headers, and consistency between committed evidence and the executable protocol.

## Separation of evidence

`scripts/run_demo.py` exercises synthetic fixtures. `scripts/run_sciq_study.py` produces the real external-data research evidence. The two evidence layers must not be conflated.
