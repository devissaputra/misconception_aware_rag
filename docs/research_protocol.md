# Research protocol

## Project

Misconception-Aware RAG Tutor

## Questions

1. Does misconception-aware retrieval improve pedagogical relevance compared with generic retrieval?
2. How can explanations remain grounded in approved course evidence?
3. How should uncertainty be surfaced when evidence is insufficient?

## Baseline methods

- token overlap retrieval
- normalized lexical scoring
- misconception cue matching
- zero overlap filtering
- evidence ID return

## Evidence to collect

Start from the current transparent baseline and record every transformation needed to produce misconception labels plus IDs and text for retrieved evidence passages. Keep a clear boundary between synthetic demonstration data and any future empirical dataset.

## Validation

Measure retrieval recall and precision on labeled evidence, then evaluate misconception detection separately. If generation is added later, score citation support and answer faithfulness against the retrieved corpus.

## What counts as a useful result

The next study should use a labeled set of questions, misconceptions, and source passages. Lexical retrieval can then be compared with embedding and reranking baselines before any answer generation is evaluated.

## Threats to validity

Surface word overlap, incomplete misconception dictionaries, ambiguous learner language, and missing course evidence can all produce weak retrieval.
