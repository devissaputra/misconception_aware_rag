# Related work and technical context

Misconception-Aware RAG Tutor is an original transparent implementation.

It does not reproduce the models or empirical results below.

## Retrieval-augmented generation

Lewis et al. introduced a general retrieval-augmented generation framework that combines parametric sequence generation with retrieved non-parametric evidence.

- Lewis, P., Perez, E., Piktus, A., et al. (2020).
- *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.*
- https://arxiv.org/abs/2005.11401

The current repository follows the broad retrieve-then-generate structure, but uses:

- BM25 rather than a dense neural retriever
- a structured misconception catalog
- deterministic template generation rather than a trained seq2seq or LLM generator

It should therefore be read as a transparent educational RAG baseline, not as an implementation of the original RAG architecture.

## MisEdu-RAG

Guo, Xue, Lu, and Lin propose MisEdu-RAG, a misconception-aware dual-hypergraph RAG framework for novice math teachers.

The method organizes pedagogical knowledge and student mistake cases into connected structures, performs multi-stage retrieval, and generates guidance grounded in retrieved evidence.

- Guo, Z., Xue, R., Lu, Y., & Lin, J. (2026).
- *MisEdu-RAG: A Misconception-Aware Dual-Hypergraph RAG for Novice Math Teachers.*
- arXiv:2604.04036
- https://arxiv.org/abs/2604.04036

This repository is substantially simpler.

It does not implement hypergraphs, learned retrieval, an LLM generator, or teacher-study validation.

The useful comparison is architectural: learner mistake evidence should influence what is retrieved rather than sit beside retrieval as an unused label.

## Misconception diagnosis by generate-retrieve-rerank

Recent work on misconception diagnosis from student-tutor dialogue explores a generate, retrieve, and rerank pipeline for candidate misconceptions.

- Mitton, J., Bhattacharyya, P., Smith, D., Christie, T., Abboud, R., & Woodhead, S. (2026).
- *Misconception Diagnosis From Student-Tutor Dialogue: Generate, Retrieve, Rerank.*
- arXiv:2602.02414
- https://arxiv.org/abs/2602.02414

That work reinforces the importance of evaluating misconception identification separately from evidence retrieval.

The current repository instead uses a hand-authored cue catalog so every diagnostic rule remains inspectable.

## Current scope

Implemented:

- structured misconception catalog
- positive and rejection cues
- possible/rejected/ambiguous detections
- misconception-conditioned query expansion
- BM25 generic retrieval
- pedagogical reranking
- explicit score breakdown
- preferred corrective evidence retrieval
- evidence sufficiency checks
- abstention
- deterministic citation-grounded response generation
- detection precision/recall/F1
- Precision@k
- Recall@k
- reciprocal rank
- nDCG@k
- CSV loaders
- synthetic generic-vs-aware comparison

Not implemented:

- dense embeddings
- vector database
- neural reranker
- hypergraph retrieval
- learned misconception detector
- LLM generation
- dialogue-state model
- automatic citation-faithfulness model
- validated confidence calibration
- production learner model
- empirical teacher or learner study

The project is best understood as a reproducible misconception-aware educational RAG baseline whose individual components can be replaced and evaluated separately.
