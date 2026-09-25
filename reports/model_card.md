# Analytic System Card

## System

Misconception-Aware RAG Tutor with a separate empirical SciQ retrieval study.

## Current maturity

Research prototype. The empirical layer supports bounded claims about lexical evidence retrieval; the diagnostic/tutoring layer remains synthetic-fixture software research.

## Empirical evidence

The SciQ study compares question-only BM25, observed wrong-answer conditioning, a shuffled wrong-answer lexical-expansion control and an oracle-informed gold-answer sensitivity condition. It does not validate misconception diagnosis or tutoring effectiveness.

The shuffled control preserves the distractor-text distribution while breaking question–answer alignment. It is designed to expose generic query-expansion effects.

## Prototype inputs and outputs

The prototype accepts task context and learner response, can emit possible/rejected/ambiguous misconception hypotheses, performs lexical retrieval and pedagogical reranking, checks evidence sufficiency, and either abstains or composes a deterministic citation-grounded response.

## Main limitations

- cue matching can miss paraphrases;
- a wrong answer need not imply a stable misconception;
- synthetic fixture cues are not population-validated;
- BM25 is lexical;
- metadata boosts and evidence-sufficiency thresholds are unvalidated;
- deterministic generation is limited;
- retrieval relevance is not pedagogical effectiveness;
- SciQ support passages are not a real classroom knowledge base;
- the shuffled control does not identify learner cognitive mechanisms.

## Human oversight

Misconception hypotheses should remain inspectable, reversible and non-consequential unless supported by substantially stronger learner-level evidence and governance.
