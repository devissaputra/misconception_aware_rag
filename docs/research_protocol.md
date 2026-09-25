# Research Protocol

## Empirical question

Does adding an observed wrong-answer option to a science question change BM25 retrieval of the question's supporting evidence, and is that effect distinguishable from adding unrelated distractor-like text?

## Dataset

Frozen SciQ external test split. See `DATA.md` for revision and SHA-256.

## Unit and dependence

A question is the uncertainty-resampling unit. Each eligible question contributes three wrong-answer proxy cases, one per distractor. Cases belonging to the same question are never treated as independent bootstrap units.

## Conditions

1. **question_only** — question text only.
2. **wrong_answer_conditioned** — question plus the observed SciQ distractor.
3. **shuffled_wrong_answer_control** — question plus same-position distractor text from another eligible question under a frozen derangement.
4. **oracle_corrective** — question plus observed distractor plus gold correct answer; oracle-informed sensitivity only.

The shuffled condition preserves the marginal distractor-text distribution and controls for generic lexical expansion. The oracle condition is not a mathematical upper bound.

## Retrieval protocol

BM25 uses `k1=1.5`, `b=0.75`, Unicode lowercased word tokens and depth `k=5`.

## Outcomes

MRR, Recall@1/3/5 and nDCG@5. Three question-block bootstrap contrasts are reported: wrong vs question-only, shuffled vs question-only, and wrong vs shuffled. Directional improve/worsen/tie counts supplement mean effects.

## Non-claim

SciQ distractors are not validated learner misconceptions. The empirical study evaluates retrieval conditioning, not diagnosis or learning outcomes.

## Prototype research path

The separate prototype retains possible/rejected/ambiguous cue detection, query expansion, BM25, pedagogical reranking, evidence sufficiency, abstention and deterministic grounded generation. Future diagnostic research requires independently validated misconception taxonomies and real learner data.
