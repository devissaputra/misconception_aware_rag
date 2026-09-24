# Ethics, safety, and misuse risks

## Intended use

Misconception-Aware RAG Tutor is a research prototype for studying misconception-conditioned educational retrieval and grounded tutoring responses.

It is not a psychological assessment, learner-ranking system, grading system, or autonomous diagnosis engine.

## A misconception label is a hypothesis

A learner response can be wrong for many reasons:

- a stable misconception
- a one-off slip
- incomplete knowledge
- ambiguous wording
- unfamiliar terminology
- language/translation difficulty
- alternative reasoning
- transcription error
- misunderstanding the question

The system should therefore say **possible misconception** or **evidence consistent with** rather than asserting that a learner "has" a misconception.

## Mentioning is not believing

A learner may quote or reject an incorrect statement.

For example:

- "Plants do not respire." may be evidence for a candidate misconception.
- "It is false that plants do not respire." is not the same thing.

The current synthetic catalog contains explicit negative/rejection cues to exercise this distinction.

Real dialogue requires stronger contextual modeling.

## Misdiagnosis risk

False misconception labels can redirect instruction away from the learner's actual need and may create misleading learner profiles.

Do not persist misconception labels as durable learner traits without strong evidence, review, and a clear educational purpose.

## Correction backfire and over-explanation

A correction can be technically accurate yet pedagogically poor.

Risks include:

- repeating the misconception without a clear correction
- giving the complete solution too early
- overwhelming the learner with evidence
- removing productive struggle
- presenting one strategy as mandatory
- correcting an interpretation that was actually valid

Human or learner-controlled review remains important.

## Evidence-source risk

Retrieval grounding only helps when the evidence source is trustworthy and appropriate.

A retrieved passage may be:

- outdated
- incomplete
- out of scope
- poorly chunked
- pedagogically unsuitable
- copyrighted or restricted
- inconsistent with the current curriculum

Store source/version metadata and review the evidence corpus.

The synthetic `authority` field is not a truth probability.

## Preferred-evidence leakage

The synthetic misconception catalog lists preferred evidence IDs so the code path for misconception-specific evidence can be tested.

In a real evaluation, gold relevance labels must be separated from production retrieval metadata.

Otherwise the system can appear strong because evaluation answers leaked into the retriever.

## Abstention

The system should be able to say that evidence is insufficient.

Do not force a misconception-specific response when:

- no candidate is supported
- relevant course evidence is missing
- retrieved evidence conflicts
- the learner response is ambiguous
- the task context is insufficient

## Generation risk

The current generator is deterministic and citation-grounded.

If an LLM is added later, additional risks include:

- unsupported claims
- fabricated citations
- invented learner reasoning
- overconfident diagnosis
- trace leakage
- answer leakage that bypasses learning

The generator should never be trusted merely because retrieval is present.

## Privacy

Learner explanations and tutoring dialogue can contain educational records and sensitive personal information.

Do not commit identifiable learner responses, private tutor dialogue, grades, accommodations, disability/health information, or restricted LMS data.

Use data minimization, de-identification, documented retention, and access controls.

## Excluded uses

Do not use this prototype alone for:

- grading
- admissions
- discipline
- employment decisions
- psychological diagnosis
- disability diagnosis
- covert surveillance
- permanent learner profiling
- deciding intelligence or ability
- automatic course placement

## Before real-user research

Document:

- misconception taxonomy
- annotation guidelines
- annotator expertise
- evidence corpus authority
- corpus versioning
- relevance judgments
- diagnostic uncertainty
- abstention policy
- correction strategy
- learner/tutor override
- privacy controls
- accessibility
- adverse-error review

The goal is to support careful instructional reasoning, not convert learner errors into fixed labels.
