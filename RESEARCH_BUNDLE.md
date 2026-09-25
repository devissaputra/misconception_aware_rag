# Research Bundle Evidence Contract

## Identity

**Area:** AI in Education  
**Study:** wrong-answer-conditioned educational evidence retrieval with lexical-expansion negative control  
**External dataset:** SciQ

## Primary research question

Does adding an observed wrong-answer option change BM25 retrieval of the question's support passage relative to question-only retrieval, and is that effect distinguishable from adding unrelated distractor-like text?

## Required evidence

A valid full run must record:

1. pinned dataset repository, revision, file, license and SHA-256;
2. expected and observed test-row count;
3. eligible question count and unique support-document count;
4. three wrong-answer proxy cases per eligible question;
5. BM25 `k1`, `b`, retrieval depth and tokenization rule;
6. question-only, observed-wrong-answer, shuffled-control and oracle-informed conditions;
7. deterministic shuffled-control seed and proof-by-construction of no self-matches;
8. MRR, Recall@1/3/5 and nDCG@5 for every condition;
9. question-block paired uncertainty for observed wrong answer vs question only;
10. question-block paired uncertainty for shuffled control vs question only;
11. question-block paired uncertainty for observed wrong answer vs shuffled control;
12. directional improve/worsen/tie analysis;
13. mean query-token counts by condition;
14. Python, pandas, pyarrow and platform versions;
15. machine-readable, Markdown and LaTeX generated results;
16. explicit distinction between wrong-answer proxies and validated misconceptions.

## Comparison roles

- **question_only:** primary baseline.
- **wrong_answer_conditioned:** primary treatment.
- **shuffled_wrong_answer_control:** lexical-expansion negative control.
- **oracle_corrective:** oracle-informed sensitivity condition only; not an upper bound and not deployable.

## Evidence-integrity rule

CI must fail if committed empirical artifacts no longer match the frozen source identity or executable protocol.

## Non-claims

The study does not validate learner misconception diagnosis, pedagogical effectiveness, causal learning gains, an LLM tutor, semantic citation faithfulness, or production readiness. Synthetic fixtures remain software-regression evidence only.
