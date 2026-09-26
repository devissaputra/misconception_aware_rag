# Misconception-Aware RAG Tutor — Empirical

This repository separates an empirical retrieval study from the tutoring prototype built around it. The study tests whether conditioning evidence retrieval on an observed wrong answer changes support-passage retrieval on SciQ, while a negative-control condition checks whether any gain is more than the effect of simply appending extra distractor-like text.

Wrong-answer expansion slightly reduces MRR from 0.9472 to 0.9433 in the frozen benchmark. Its contrast with a shuffled distractor control has an interval spanning zero, so the study does not establish a distinct benefit from the semantic relationship of the wrong answer. The repository therefore separates the measured retrieval result from the tutoring prototype and makes no claim of improved learning.

See [CALCULATIONS.md](CALCULATIONS.md) for evidence and verification scope.
