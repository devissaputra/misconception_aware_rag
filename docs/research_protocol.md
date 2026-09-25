# Research Protocol

## Empirical study

### Question

Does adding an observed wrong-answer option to a science question change BM25 retrieval of the question's supporting evidence?

### Dataset

SciQ external test split, pinned and SHA-256 verified. See `DATA.md`.

### Unit and dependence

A question is the uncertainty-resampling unit. Each eligible question contributes three wrong-answer proxy cases, one per distractor. Bootstrap resampling therefore occurs by question block.

### Conditions

1. question-only BM25;
2. question + wrong-answer proxy;
3. question + wrong-answer proxy + gold correct answer (oracle sensitivity only).

### Outcomes

MRR, Recall@1/3/5 and nDCG@5. Directional analysis counts cases where wrong-answer conditioning improves, worsens or ties question-only retrieval.

### Non-claim

SciQ distractors are not validated learner misconceptions. This study evaluates wrong-answer-conditioned retrieval only.

## Prototype research path

The repository also keeps the inspectable tutoring prototype: possible/rejected/ambiguous cue detection, query expansion, BM25, pedagogical reranking, evidence sufficiency, abstention and deterministic grounded response generation.

The small committed CSV catalog is a software fixture. Future diagnostic research should independently validate misconception taxonomies, annotation quality, false positives, retrieval relevance, grounding and pedagogical usefulness on held-out real learner data.
