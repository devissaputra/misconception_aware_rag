# Dataset Card — SciQ External Empirical Benchmark

## Source

**Dataset:** SciQ  
**Repository:** Allen Institute for AI / `allenai/sciq`  
**Paper:** Welbl, J., Liu, N. F., & Gardner, M. (2017). *Crowdsourcing Multiple Choice Science Questions*. arXiv:1707.06209  
**License reported by dataset card:** CC BY-NC 3.0

## Frozen executable source

- revision: `2c94ad3e1aafab77146f384e23536f97a4849815`
- file: `data/test-00000-of-00001.parquet`
- expected SHA-256: `3a719356a29b127fc54ef3c7f51a034db4bd105d5717215e8c85d2aa58d60667`

Every empirical run verifies this byte-level identity and the expected 1,000-row test size before analysis.

## Fields used

`question`, `distractor1`, `distractor2`, `distractor3`, `correct_answer`, and `support`.

Only rows with a non-empty support paragraph enter the study. Unique support paragraphs become retrieval documents; a question's own support paragraph is its relevant document.

## Wrong-answer proxy cases

Each eligible question contributes three observed wrong-answer proxy cases, one for each SciQ distractor. A distractor is an incorrect answer option—not an expert-validated learner misconception.

## Shuffled lexical-expansion control

For each distractor position, the runner constructs a deterministic derangement of eligible question indices using seed `20260925`. Each question receives distractor text from a **different** question, with no self-match. Across the full control, every distractor text at that position is used exactly once.

This preserves the marginal distractor-text distribution while breaking the relationship between the question and appended wrong-answer text. It is a negative control for generic query-expansion effects, not a synthetic learner response.

## Oracle-informed condition

The gold correct answer is used only in `oracle_corrective`. This is an oracle-informed sensitivity condition, **not** a mathematical upper bound and not a deployable method.

## Output privacy / redistribution boundary

Generated per-case output stores question indices, distractor indices, shuffled source indices, query-token counts and retrieval metrics. It does not commit SciQ question, answer or support text.

## Synthetic fixtures

The small CSV files under `data/` remain synthetic software fixtures for prototype tests and demonstrations. They are not empirical learner evidence.
