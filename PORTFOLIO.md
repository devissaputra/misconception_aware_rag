# Portfolio Positioning

**Primary tag:** AI in Education  
**Artifact type:** Empirical Research Bundle  
**Research theme:** educational evidence retrieval, wrong-answer conditioning, negative-control evaluation, reproducibility  
**External data:** frozen SciQ test split

The professor-facing contribution is the controlled SciQ retrieval study, not a claim that the full tutor is validated. The study separates question-only retrieval, observed wrong-answer conditioning, a shuffled distractor lexical-expansion control, and an oracle-informed sensitivity condition. Its main result is negative but useful: both real and shuffled distractor expansion reduce MRR relative to question-only retrieval, while the observed-vs-shuffled contrast is not clearly separated from zero under question-block bootstrap uncertainty.

The separate tutor prototype demonstrates inspectable engineering for misconception hypotheses, pedagogical reranking, evidence sufficiency, abstention and deterministic citation-grounded responses, while remaining explicitly outside the empirical claim boundary.

Recommended review path: README.md → DATA.md → scripts/run_sciq_study.py → results/summary.md → results/metrics.json → RESEARCH_BUNDLE.md → paper/paper.md → tests/test_sciq_study.py.
