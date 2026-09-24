# Misconception-Aware RAG Tutor

> Misconception-conditioned educational retrieval with BM25 ranking, pedagogical reranking, evidence sufficiency, abstention, and citation-grounded tutor response generation.

[![CI](https://github.com/devissaputra/misconception_aware_rag/actions/workflows/ci.yml/badge.svg)](https://github.com/devissaputra/misconception_aware_rag/actions/workflows/ci.yml)

![Misconception-Aware RAG Tutor architecture](assets/architecture.svg)

**Area:** AI in Education · Educational RAG · Misconception Support  
**Status:** working research prototype  
**Author:** Devis Wawan Saputra

## Why this project exists

A tutor should not merely detect a possible misconception and then retrieve unrelated evidence.

The misconception signal should actually change:

- what the system searches for
- which course passages are prioritized
- whether corrective evidence is available
- whether the system should answer or abstain
- how the response communicates uncertainty

This repository implements that full path.

The current response generator is deterministic and citation-grounded.

It is **not an LLM**.

## Implemented pipeline

![Misconception-Aware RAG Tutor data flow](assets/data_flow.svg)

The current pipeline is:

```text
task question
      +
learner response
      ↓
possible misconception detection
      ↓
misconception-conditioned query expansion
      ↓
BM25 retrieval
      ↓
pedagogical reranking
      ↓
evidence sufficiency
      ↓
grounded response or abstention
```

Each stage is separately inspectable and separately evaluable.

## Task question and learner response are separate

The system does not treat every mention of an incorrect statement as learner belief.

For example:

```text
Learner response:
"Plants do not respire."
```

can trigger a possible misconception candidate.

But:

```text
Learner response:
"It is false that plants do not respire."
```

should not be treated the same way.

The structured misconception catalog therefore supports both positive cues and rejection cues.

## Structured misconception catalog

Each `MisconceptionRecord` stores:

- misconception ID
- concept
- canonical statement
- description
- positive cues
- negative/rejection cues
- corrective concepts
- remediation guidance
- preferred evidence IDs

Detection returns one of:

- `possible`
- `rejected`
- `ambiguous`

The system uses **possible misconception** rather than claiming that a learner definitely holds a misconception.

## Misconception-conditioned retrieval

This is the central difference from the original prototype.

Originally:

```text
misconception detection ──┐
                          ├── independent outputs
lexical retrieval ────────┘
```

The detected misconception never influenced retrieval.

That is now fixed.

Possible misconception candidates contribute:

- concept expansion
- corrective-concept expansion
- preferred evidence IDs
- evidence-kind priorities
- reranking boosts

Rejected and ambiguous detections do not activate the same misconception-specific retrieval boosts.

## Generic BM25 baseline

`retrieve_generic()` implements a transparent BM25 baseline.

Unlike the original raw-overlap score, BM25 includes:

- term frequency
- inverse document frequency
- document-length normalization

Zero-relevance passages are not padded into the output.

## Pedagogical reranking

`retrieve_misconception_aware()` adds transparent reranking signals on top of BM25.

The score breakdown includes:

- `bm25_score`
- `misconception_boost`
- `kind_boost`
- `authority_boost`
- `final_score`

The current evidence kinds are:

- explanation
- counterevidence
- worked example
- remediation
- definition

The synthetic `authority` field is metadata for testing.

It is **not** a probability that a source is true.

## Evidence with zero lexical overlap

Corrective evidence can use different wording from the learner's incorrect statement.

For that reason, preferred misconception evidence can enter the candidate set even when lexical overlap is zero.

This behavior is explicit and inspectable rather than hidden inside a learned reranker.

## Evidence sufficiency and abstention

`assess_evidence_sufficiency()` evaluates whether the system has enough support to generate a misconception-specific response.

Current checks include:

- minimum number of evidence passages
- minimum top evidence score
- explanatory or counterevidence support when a misconception is active

When those checks fail, the system can return:

```text
status = abstain
```

rather than forcing a correction.

The thresholds are research assumptions and need empirical validation.

## Citation-grounded generation

`generate_grounded_tutor_response()` completes the retrieval-to-generation path.

The current generator is deterministic.

It:

- describes misconception detections as possible
- cites retrieved document IDs
- includes retrieved evidence passages
- asks the learner to check reasoning against the evidence
- abstains when evidence is insufficient

Example structure:

```text
A possible misconception is ...
Relevant course evidence:
[D01] ...
[D03] ...
Check your reasoning against these cited passages ...
```

This is a reproducible generation baseline, not an LLM.

A future LLM can replace the generator boundary only when the retrieval and grounding evaluation are ready.

## Synthetic research corpus

![Misconception-Aware RAG synthetic demo](assets/demo_snapshot.svg)

The repository now includes:

- **24 synthetic evidence passages**
- **8 structured misconception records**
- **16 labeled learner-response cases**
- rejection and negation cases
- clean/correct responses
- expected misconception labels
- relevant evidence IDs

Covered concepts include:

- plant respiration
- photosynthesis
- force and motion
- fractions
- correlation and causation
- while loops
- independent probability
- heat and temperature

All records are synthetic.

## Demo comparison

The demo compares:

```text
generic BM25
vs
misconception-aware BM25 + pedagogical reranking
```

on the same labeled cases.

It prints:

- expected misconception labels
- predicted misconception labels
- generic top-3 evidence
- misconception-aware top-3 evidence
- response status
- citation IDs

It also summarizes synthetic component diagnostics.

Those values are software test results, **not empirical learner-study findings**.

## Evaluation metrics

### Misconception detection

Implemented:

- precision
- recall
- F1

Future real studies should also report false positives separately for:

- explicit rejection
- quotation
- ambiguity
- slips/errors
- incomplete knowledge

### Retrieval

Implemented:

- Precision@k
- Recall@k
- reciprocal rank
- nDCG@k

### Response behavior

The current baseline exposes:

- grounded response vs abstention
- citation IDs
- evidence sufficiency diagnostics

The repository does **not** claim to have a semantic faithfulness scorer.

If an LLM generator is added later, evaluation should additionally include unsupported-claim rate, citation correctness, citation completeness, and pedagogical response quality.

## Run the project

```bash
git clone https://github.com/devissaputra/misconception_aware_rag.git
cd misconception_aware_rag

python scripts/run_demo.py
python -m unittest discover -s tests -v
```

The current implementation uses only the Python standard library.

## Data

`data/documents.csv`  
Synthetic evidence corpus.

`data/misconceptions.csv`  
Structured misconception catalog.

`data/cases.csv`  
Labeled evaluation cases.

`data/sample.csv`  
Small preview.

`data/README.md`  
Schema, interpretation boundaries, evaluation cautions, and real-data governance guidance.

## Core API

`EvidenceDocument`  
Structured evidence passage with concept, evidence kind, source, and authority metadata.

`MisconceptionRecord`  
Structured misconception definition with positive/rejection cues, corrective concepts, remediation, and preferred evidence.

`detect_misconceptions(...)`  
Returns possible/rejected/ambiguous misconception candidates.

`build_retrieval_query(...)`  
Adds corrective concepts for possible misconception candidates.

`retrieve_generic(...)`  
Generic BM25 baseline.

`retrieve_misconception_aware(...)`  
Misconception-conditioned BM25 retrieval plus pedagogical reranking.

`assess_evidence_sufficiency(...)`  
Determines whether evidence is strong enough for response generation.

`generate_grounded_tutor_response(...)`  
Deterministic citation-grounded response baseline.

`precision_recall_f1(...)`  
Misconception-detection metrics.

`retrieval_metrics(...)`  
Precision@k, Recall@k, reciprocal rank, and nDCG@k.

`evaluate_case(...)`  
Runs an end-to-end labeled case.

`load_documents_csv(...)` / `load_catalog_csv(...)`  
Validated CSV loaders.

Legacy `retrieve(...)`, `detect_misconception(...)`, and `grounded_response(...)` remain for backward compatibility.

## Research context

The broad RAG architecture is informed by:

- Lewis et al. (2020), *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*
- https://arxiv.org/abs/2005.11401

Misconception-aware educational RAG is directly relevant to:

- Guo et al. (2026), *MisEdu-RAG: A Misconception-Aware Dual-Hypergraph RAG for Novice Math Teachers*
- https://arxiv.org/abs/2604.04036

Recent misconception-diagnosis work also studies candidate generation, retrieval, and reranking:

- Mitton et al. (2026), *Misconception Diagnosis From Student-Tutor Dialogue: Generate, Retrieve, Rerank*
- https://arxiv.org/abs/2602.02414

See `docs/related_work.md`.

The current repository is intentionally much simpler than those learned systems.

## Evaluation checklist

![Misconception-Aware RAG evaluation checklist](assets/evaluation_dashboard.svg)

A real study should separately validate:

1. **Misconception validity** — is the learner actually expressing the annotated misconception?
2. **Retrieval quality** — are the right evidence passages ranked highly?
3. **Evidence sufficiency** — does the system abstain appropriately?
4. **Grounding** — are generated claims supported by retrieved evidence?
5. **Pedagogical usefulness** — does the response actually help learning?
6. **Leakage control** — are gold evaluation labels separated from production retrieval metadata?

## Responsible-use boundary

Do not treat:

- one wrong answer as a stable misconception
- mentioning a misconception as believing it
- a metadata authority value as truth probability
- retrieval relevance as pedagogical effectiveness
- citations as proof that every generated claim is faithful
- a synthetic benchmark result as real learner evidence

## What this repository does not implement

The current version does not include:

- dense embeddings
- vector database
- neural reranker
- hypergraph retrieval
- learned misconception classifier
- LLM generation
- dialogue-state tracking
- semantic citation-faithfulness model
- validated confidence calibration
- production learner profiles

Those are future research directions, not hidden capabilities.

## Limitations

The current baseline:

- depends on a hand-authored cue catalog
- can miss paraphrased misconceptions
- uses catalog-specific rejection cues
- uses lexical BM25 retrieval
- uses hand-authored reranking boosts
- can leak gold knowledge if preferred evidence IDs are misused in evaluation
- uses synthetic source-authority metadata
- uses unvalidated sufficiency thresholds
- uses a limited deterministic generator
- has not been tested with real learners or teachers

## Repository map

```text
.
├── .github/workflows/ci.yml
├── assets/
│   ├── README.md
│   ├── architecture.svg
│   ├── data_flow.svg
│   ├── demo_snapshot.svg
│   └── evaluation_dashboard.svg
├── data/
│   ├── README.md
│   ├── cases.csv
│   ├── documents.csv
│   ├── misconceptions.csv
│   └── sample.csv
├── docs/
│   ├── ethics_and_risks.md
│   ├── related_work.md
│   └── research_protocol.md
├── reports/model_card.md
├── scripts/run_demo.py
├── src/misconception_aware_rag/
│   ├── __init__.py
│   └── core.py
├── tests/test_core.py
├── .gitignore
├── CITATION.cff
├── LICENSE
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Research path

A stronger empirical version would:

1. create a real misconception taxonomy with expert annotation
2. distinguish misconception from slips, ambiguity, and incomplete knowledge
3. hold out evaluation cases from catalog construction
4. remove preferred evidence IDs from production retrieval when evaluating generalization
5. compare generic BM25 with misconception-aware BM25
6. add dense retrieval as an explicit separate baseline
7. add learned reranking only after labeled retrieval evaluation exists
8. evaluate abstention and evidence sufficiency
9. add a model generator behind the existing generation boundary
10. evaluate citation correctness and unsupported claims
11. measure pedagogical usefulness with teachers and learners
12. only then claim real-world misconception-aware tutoring effectiveness

## Citation and license

`CITATION.cff` contains the software citation.

Code and original SVG visuals use the MIT License. External datasets, models, publications, and educational resources retain their own licenses and usage conditions.
