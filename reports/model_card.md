# Analytic system card

## System

Misconception-Aware RAG Tutor

## Purpose

Lexical retrieval baseline that links misconception cues to course evidence without inventing unsupported answers.

## Current maturity

Working research prototype. The bundled example checks the software path with synthetic inputs. It does not establish validity for real learners, instructors, courses, or workplaces.

## Inputs

See `../data/README.md` for the current synthetic schema and the documentation expected before real data are connected.

## Outputs

The current code produces misconception labels plus IDs and text for retrieved evidence passages. These outputs are research signals and should be interpreted with the educational context that produced them.

## Evidence needed before real use

Measure retrieval recall and precision on labeled evidence, then evaluate misconception detection separately. If generation is added later, score citation support and answer faithfulness against the retrieved corpus.

## Main limitation

Cue matching and lexical overlap will miss paraphrases and can retrieve text that shares words without answering the question. The module does not verify factual completeness or generate a final tutoring response.

## Human oversight

A person must review any output before it can affect a learner, instructor, applicant, or employee.
