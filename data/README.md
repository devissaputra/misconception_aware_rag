# Data documentation

The committed CSV files in this folder are **synthetic software fixtures** for unit tests and the local prototype demo. They are not the empirical evidence for the research bundle.

## Real empirical data

The research study is run by `scripts/run_sciq_study.py`, which downloads the pinned external SciQ test parquet described in `../DATA.md`. The raw SciQ file is cached under `data/cache/`, which is gitignored.

## Fixture files

- `documents.csv` — small synthetic evidence passages;
- `misconceptions.csv` — synthetic cue/catalog records;
- `cases.csv` — synthetic evaluation cases;
- `sample.csv` — compact preview.

These fixtures exist to exercise detection, BM25 retrieval, reranking, abstention and deterministic citation generation. Their metrics are regression-test outputs, not learner-study findings.

## Boundary

Do not commit identifiable learner responses, private tutoring dialogue, grades, accommodations, health information, restricted LMS exports, proprietary course materials or copyrighted textbook chapters without permission.

A real misconception-diagnosis study requires expert annotation, adjudication, privacy governance and held-out learner data. SciQ distractors in the current empirical retrieval study are wrong-answer proxies, not validated misconception labels.
