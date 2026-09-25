# Research Bundle Evidence Contract

## Identity

**Area:** AI in Education  
**Study:** wrong-answer-conditioned educational evidence retrieval  
**External dataset:** SciQ  
**Primary comparison:** question-only BM25 versus question + observed wrong-answer proxy

## Required evidence

A valid empirical run must record:

1. pinned dataset repository, revision, file and SHA-256;
2. dataset license and paper reference;
3. number of loaded and eligible questions;
4. number of unique support documents;
5. number of wrong-answer proxy cases;
6. exact retrieval conditions;
7. MRR, Recall@1/3/5 and nDCG@5 for every condition;
8. question-block paired uncertainty for the primary MRR difference;
9. improve/worsen/tie error analysis;
10. explicit distinction between wrong-answer proxies and validated misconceptions.

## Baselines

The question-only BM25 condition is the primary baseline. The gold-correct-answer condition is an oracle sensitivity analysis and must never be presented as a production method.

## Non-claims

The study does not validate learner misconception diagnosis, pedagogical effectiveness, an LLM tutor, causal learning gains, semantic citation faithfulness, or production readiness.

The synthetic fixture benchmark remains useful for software regression tests only.
