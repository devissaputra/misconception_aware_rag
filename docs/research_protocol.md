# Research protocol

## Project

Misconception-Aware RAG Tutor

## Research questions

1. Does misconception-conditioned retrieval improve evidence recall and ranking compared with generic retrieval?
2. Can explicit positive and negative misconception cues reduce false-positive diagnosis when learners reject or quote a misconception?
3. Which evidence types are most useful for correction: explanation, counterevidence, remediation, or worked examples?
4. When should the system abstain because misconception evidence or course evidence is insufficient?
5. How should retrieval quality and response-generation quality be evaluated separately?
6. Does a future learned generator remain faithful to retrieved course evidence while preserving pedagogical usefulness?

## RAG framing

Retrieval-augmented generation combines retrieval from an external evidence store with a response-generation stage conditioned on retrieved evidence.

The current repository implements both stages, but the generation stage is deliberately a **deterministic template baseline**, not an LLM.

This keeps the complete retrieval-to-citation software path executable with the Python standard library while avoiding claims that a language model is present.

A future model can replace the deterministic generator only after retrieval, evidence sufficiency, citation behavior, and evaluation are stable.

## Current pipeline

### 1. Task question and learner response

The code keeps the task question separate from the learner response.

A question mentioning a misconception is not automatically treated as evidence that the learner believes it.

### 2. Misconception candidate detection

The synthetic misconception catalog stores:

- misconception ID
- concept
- canonical statement
- description
- positive cues
- negative/rejection cues
- corrective concepts
- remediation guidance
- preferred evidence IDs

Detection can return:

- possible
- rejected
- ambiguous

The system uses the phrase **possible misconception** rather than treating cue matching as a diagnosis.

### 3. Misconception-conditioned query construction

Possible misconceptions add corrective concepts to the retrieval query.

Rejected and ambiguous detections do not activate misconception-specific evidence boosts.

### 4. Generic BM25 baseline

`retrieve_generic()` implements transparent BM25 lexical retrieval.

This is a stronger lexical baseline than raw token overlap because it includes term frequency, inverse document frequency, and document-length normalization.

### 5. Pedagogical reranking

`retrieve_misconception_aware()` combines:

- BM25 relevance
- preferred misconception evidence
- concept alignment
- corrective-concept alignment
- evidence-kind priority
- source-authority metadata

Each returned row exposes the individual score components.

The authority field is metadata, not a probability that the passage is true.

### 6. Evidence sufficiency and abstention

`assess_evidence_sufficiency()` can reject generation when:

- too few evidence passages were retrieved
- top evidence score is below threshold
- a detected misconception lacks explanatory or counterevidence support

Thresholds are configurable research assumptions, not validated constants.

### 7. Citation-grounded generation

`generate_grounded_tutor_response()` is a deterministic response composer.

It:

- labels detections as possible, not certain
- cites retrieved evidence IDs
- includes only retrieved evidence passages in the evidence section
- abstains when evidence is insufficient

It is not an LLM and should not be evaluated as if it were one.

## Component-wise evaluation

### Misconception detection

Evaluate:

- precision
- recall
- F1
- false positives on rejection/negation cases
- performance by misconception type

A real study should also distinguish misconception from isolated error, incomplete knowledge, and ambiguous language.

### Retrieval

Evaluate:

- Precision@k
- Recall@k
- reciprocal rank
- nDCG@k
- evidence-type coverage
- misconception-relevant retrieval recall

Compare at minimum:

- generic BM25
- misconception-aware BM25 + pedagogical reranking

Future work may add dense retrieval and learned reranking.

### Evidence sufficiency

Evaluate:

- appropriate abstention when evidence is absent
- unnecessary abstention when relevant evidence is available
- sensitivity to threshold choices

### Generation

For the current deterministic generator evaluate:

- citation validity
- citation coverage
- whether cited passages are actually retrieved
- abstention behavior
- whether diagnosis language remains appropriately uncertain

If an LLM generator is added, also evaluate:

- unsupported-claim rate
- citation correctness
- citation completeness
- faithfulness
- misconception-correction accuracy
- pedagogical usefulness

## Synthetic baselines

The bundled data are designed to exercise software behavior rather than produce publishable performance claims.

The demo compares generic and misconception-aware retrieval on the same synthetic cases.

Any observed difference is a test-fixture result only.

## Threats to validity

Important threats include:

- cue dictionaries missing paraphrases
- explicit cues overfitting synthetic wording
- negation and quotation ambiguity
- incorrect misconception taxonomy
- confusing misconception with a one-off mistake
- BM25 lexical mismatch
- metadata boosts dominating genuine relevance
- preferred evidence IDs leaking annotation knowledge into evaluation
- incorrect or incomplete course evidence
- source authority being mis-specified
- evaluation relevance judgments being subjective
- synthetic cases being much easier than real tutoring dialogue

A real study should separate catalog construction, retrieval development, and held-out evaluation data to avoid leakage.
