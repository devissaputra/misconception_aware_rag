# Reproducibility Protocol

## Install and test

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/run_demo.py
```

## Real-data empirical run

```bash
python scripts/run_sciq_study.py
```

The runner downloads one pinned SciQ parquet file, verifies its expected SHA-256, constructs a retrieval corpus from non-empty support paragraphs, evaluates all three distractors as wrong-answer proxy cases and generates result artifacts.

## Frozen source

Revision: `2c94ad3e1aafab77146f384e23536f97a4849815`  
Test parquet SHA-256: `3a719356a29b127fc54ef3c7f51a034db4bd105d5717215e8c85d2aa58d60667`

## Generated evidence

- `results/metrics.json`
- `results/per_case_metrics.csv`
- `results/summary.md`
- `paper/results.md`

The bootstrap resamples question blocks rather than treating each distractor case as independent.

## Separation of evidence

`scripts/run_demo.py` exercises synthetic fixtures and is a software demonstration. `scripts/run_sciq_study.py` produces the real external-data research evidence. These roles must not be conflated.
