# Dataset Card — SciQ External Empirical Benchmark

## Source

Dataset: SciQ  
Curators: Allen Institute for AI / original authors Welbl, Liu & Gardner  
Hugging Face repository: https://huggingface.co/datasets/allenai/sciq  
Paper: Welbl, J., Liu, N. F., & Gardner, M. (2017). *Crowdsourcing Multiple Choice Science Questions*. arXiv:1707.06209  
License reported by the dataset card: CC BY-NC 3.0.

## Frozen executable source

The empirical runner uses only the test parquet at:

- revision: `2c94ad3e1aafab77146f384e23536f97a4849815`
- file: `data/test-00000-of-00001.parquet`
- expected SHA-256: `3a719356a29b127fc54ef3c7f51a034db4bd105d5717215e8c85d2aa58d60667`

The runner refuses to proceed if the downloaded bytes do not match that hash.

## Fields used

- `question`
- `distractor1`
- `distractor2`
- `distractor3`
- `correct_answer`
- `support`

Only rows with non-empty support text enter the empirical retrieval study.

## Study transformation

Each unique support paragraph becomes one retrieval document. Each question contributes up to three wrong-answer proxy cases, one for each distractor. The correct answer is used only in the explicitly labeled oracle sensitivity condition.

No raw SciQ text is committed into generated per-case result files; the output stores indices and metrics.

## Critical semantic boundary

SciQ distractors are crowdsourced incorrect answer options, not expert-validated learner misconceptions. They are used as observable wrong-answer proxies to test retrieval conditioning. The study makes no claim about misconception diagnosis.

## Synthetic fixtures

The CSV files committed under `data/` remain small synthetic fixtures for unit tests and prototype demonstrations. They are not empirical research data and must not be quoted as real learner evidence.
