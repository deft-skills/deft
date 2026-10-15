---
name: user-stories
description: Use when functional requirements must be written as user stories with Given/When/Then acceptance criteria.
license: GPL-3.0-only (includes third-party material; see LICENSE-*.txt)
metadata:
  deft-version: 0.1.0
  deft-lineage: specify-requirements > specify-functional > user-stories
  deft-inputs: 'request: FeatureRequest [1]'
  deft-outputs: 'requirements: UserStory [1..*]'
  deft-origin: github/spec-kit@b9e08bf templates/commands/specify.md (MIT, adapted); github/spec-kit@b9e08bf templates/commands/clarify.md (MIT, adapted)
---

# Specify user stories

## Inputs and outputs

- Input `request`: FeatureRequest (one)
  A change request stated by a stakeholder in natural language.
  - `text` (required)
  - `system` (optional): existing system and stack
- Output `requirements`: UserStory (one or more)
  Connextra user story with Given/When/Then acceptance criteria.
  - `id` (required)
  - `text` (required)
  - `source` (required): stakeholder or document the requirement comes from
  - `role` (required)
  - `goal` (required)
  - `benefit` (required)
  - `acceptanceCriteria` (one or more)

## Before you start

- The feature request is not empty.

## Identify sources and stakeholders
<!-- deft: final section 'elicit'; declared by specify-requirements -->

1. Read the feature request and, if it exists, the project constitution or
   equivalent principles document.
2. List the stakeholders the request affects (users, operators, external
   systems) and the sources you rely on for each statement.
3. Extract the key concepts: actors, actions, data and constraints.
4. Write down the assumptions you make where the request is silent. Use
   reasonable industry defaults; do not ask about them.

## Resolve ambiguities
<!-- deft: final section 'clarify'; declared by specify-requirements -->

Mark an aspect `[NEEDS CLARIFICATION: <question>]` only when the choice
changes scope or user experience, has several reasonable interpretations,
and has no reasonable default. Keep at most three markers, ordered by
impact: scope, then security and privacy, then user experience, then
technical details.

For each marker, ask one question with two to four options and their
implications, wait for the answers, and replace the marker with the
decision. Record each decision under "Clarifications" with the date.

## Structure each requirement
<!-- deft: default section 'structure'; declared abstract by specify-requirements, implemented by user-stories -->

Write each requirement as a user story:

`As a <role>, I want <goal>, so that <benefit>.`

Follow the Quality User Story criteria: the story is well-formed (role and
goal present), atomic, minimal (no notes or design in the story), problem
oriented, and unambiguous. Give the story an id `US-<n>`.

Add one or more acceptance criteria per story, each in the form
`Given <context>, when <event>, then <outcome>`. Each criterion checks one
outcome and uses concrete values (for example "15 minutes", not "soon").

## Validate the requirements
<!-- deft: default section 'validate'; declared by specify-requirements, extended by user-stories -->

Check every requirement against this list and fix it until all items
pass (at most three iterations; then record what is still open):

- It states what is needed and why, not how to build it.
- It is atomic: one need per requirement.
- It is testable: a test can pass or fail against it.
- It is unambiguous: no vague terms such as "fast", "easy" or "robust".
- It does not conflict with or duplicate another requirement.

Also check that the stories are independent, negotiable, valuable,
estimable, small and testable (INVEST), and that every acceptance
criterion can be turned into an automated scenario without new decisions.

## Record the specification
<!-- deft: final section 'record'; declared by specify-requirements -->

Write the requirements to `specs/<feature>/requirements.md`, one block per
requirement, with its id, source and the fields of its notation. Add the
assumptions and the clarifications at the end. Report the file path and
the number of requirements per notation.

## Done when

- Every requirement has a unique id and names its source.
- Every requirement is testable and unambiguous.
- No open clarification markers remain.
- Every functional requirement describes observable behaviour of the system.
- Every user story has at least one acceptance criterion in Given/When/Then form.
