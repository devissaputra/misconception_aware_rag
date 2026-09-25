# Analytic System Card

## System

Misconception-Aware RAG Tutor

## Current maturity

Research prototype with a real external retrieval study and synthetic fixtures for the diagnostic/tutoring components.

## Empirical evidence available

The external SciQ study evaluates one bounded claim: whether adding an observed wrong-answer option changes BM25 retrieval of a support passage. It does not validate misconception diagnosis or tutoring effectiveness.

SciQ distractors are treated as wrong-answer proxies. The correct-answer-expanded condition is an oracle sensitivity analysis only.

## Prototype inputs and outputs

The prototype accepts task context and learner response, can emit possible/rejected/ambiguous misconception hypotheses, performs lexical retrieval and pedagogical reranking, checks evidence sufficiency, and either abstains or composes a deterministic citation-grounded response.

## Main limitations

- cue matching can miss paraphrases;
- a wrong answer need not imply a stable misconception;
- synthetic fixture cues are not population-validated;
- BM25 is lexical;
- metadata boosts require validation;
- evidence-sufficiency thresholds are unvalidated;
- deterministic generation is limited;
- retrieval relevance is not pedagogical effectiveness;
- the SciQ support corpus is not a real classroom knowledge base.

## Human oversight

Misconception hypotheses should remain inspectable and reversible. No output should become a durable learner label or consequential decision without stronger evidence and governance.
