# Analytic system card

## System

Misconception-Aware RAG Tutor

## Purpose

Transparent misconception-conditioned educational retrieval with evidence sufficiency, abstention, and citation-grounded tutor response generation.

## Current maturity

Working research prototype.

All bundled documents, misconception records, relevance judgments, authority values, and learner responses are synthetic.

The demo validates software behavior and component metrics; it does not establish diagnostic or pedagogical validity.

## Inputs

### Task context

- task question
- learner response

These are kept separate because mentioning a misconception in a question is not the same as expressing it as an answer.

### Misconception catalog

Each record contains:

- ID
- concept
- canonical statement
- description
- positive cues
- negative/rejection cues
- corrective concepts
- remediation text
- preferred evidence IDs

### Evidence corpus

Each passage contains:

- document ID
- concept
- evidence kind
- text
- source
- authority metadata

## Misconception outputs

Cue-level detection can return:

- possible
- rejected
- ambiguous

The system should not describe these as confirmed learner diagnoses.

## Retrieval

The repository contains:

- generic BM25 retrieval
- misconception-conditioned query construction
- concept/evidence-aware reranking
- per-result score breakdown

The misconception signal now changes retrieval behavior.

## Evidence sufficiency

Before generation, the code checks:

- evidence count
- top evidence score
- explanatory/counterevidence availability for detected misconceptions

Insufficient evidence produces abstention.

## Generation

The current generator is deterministic.

It cites retrieved evidence IDs and composes a transparent tutor response from retrieved passages.

It is **not an LLM**.

A future learned generator should be evaluated separately for unsupported claims and citation faithfulness.

## Evaluation

Implemented component metrics include:

### Misconception detection

- precision
- recall
- F1

### Retrieval

- Precision@k
- Recall@k
- reciprocal rank
- nDCG@k

### Response behavior

- grounded response vs abstention
- citation IDs returned

The current code does not implement a semantic faithfulness scorer.

## Main limitations

- cue matching misses paraphrases
- negative cues are catalog-specific
- BM25 remains lexical
- preferred evidence metadata can cause evaluation leakage if misused
- authority metadata is manually supplied
- evidence sufficiency thresholds are unvalidated
- deterministic generation is limited and repetitive
- no learned dialogue reasoning
- no empirical learner validation

## Human oversight

Misconception detections should remain hypotheses.

A teacher, tutor, researcher, or learner should be able to inspect:

- which cue fired
- whether rejection cues were present
- how retrieval was expanded
- why each evidence passage ranked highly
- whether the system abstained
- which passages support the generated response

No output should become a permanent learner label without stronger evidence and governance.
