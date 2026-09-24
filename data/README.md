# Data documentation

All data in this folder are synthetic and created for software tests and demonstrations.

## Files

- `documents.csv` — 24 course-evidence passages across eight concepts.
- `misconceptions.csv` — eight structured misconception records.
- `cases.csv` — 16 learner-response evaluation cases with expected misconception labels and relevant evidence IDs.
- `sample.csv` — compact human-readable preview retained for quick inspection.

No real learner records or copyrighted textbook passages are included.

## Evidence-document schema

`documents.csv` contains:

- `doc_id`
- `concept`
- `kind`
- `text`
- `source`
- `authority`

Supported evidence kinds are:

- explanation
- counterevidence
- worked_example
- remediation
- definition

`authority` is a synthetic 0–1 metadata value used only to exercise the reranking path. It is not a factual-truth probability.

## Misconception schema

`misconceptions.csv` contains:

- `misconception_id`
- `concept`
- `canonical_statement`
- `description`
- `positive_cues`
- `negative_cues`
- `corrective_concepts`
- `remediation`
- `evidence_ids`

Pipe-separated positive and negative cues are explicit catalog rules.

A positive cue supports a **possible misconception** signal.

A negative cue records language that rejects or corrects that misconception.

If both cue types appear in the same response the detector returns `ambiguous` rather than asserting that the learner holds the misconception.

## Evaluation cases

`cases.csv` contains:

- task question
- learner response
- expected misconception IDs
- relevant evidence IDs
- case type

The cases deliberately include:

- positive misconception examples
- explicit misconception rejection
- negated misconception statements
- clean/correct responses

This matters because a robust detector must not label a learner simply for mentioning a misconception.

## What the data do not prove

The synthetic catalog does not establish that substring/cue detection is a valid diagnostic method for real learners.

A real misconception study should distinguish at least:

- misconception
- isolated mistake or slip
- incomplete knowledge
- ambiguous language
- alternative strategy
- language/translation issue
- correct rejection of a misconception

## Before real data are connected

Document:

- domain and curriculum
- task/question source
- misconception-definition procedure
- expert annotators
- annotation guidelines
- adjudication
- evidence-source authority
- passage/chunk construction
- source version
- relevance judgments
- learner consent/privacy basis
- missingness
- language(s)
- permitted uses
- retention and access controls

## Do not commit

Do not commit identifiable learner responses, private tutoring dialogue, grades, accommodations, health information, restricted LMS exports, proprietary course materials, copyrighted textbook chapters without permission, or licensed misconception datasets that prohibit redistribution.

Keep restricted sources outside Git and store only permissible references or synthetic derivatives here.
