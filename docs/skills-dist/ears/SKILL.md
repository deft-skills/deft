---
name: ears
description: Use when functional requirements must follow the EARS (Easy Approach to Requirements Syntax) patterns.
license: GPL-3.0-only (includes third-party material; see LICENSE-*.txt)
metadata:
  deft-version: 0.1.0
  deft-lineage: specify-requirements > specify-functional > ears
  deft-inputs: 'request: FeatureRequest [1]'
  deft-outputs: 'requirements: EARSRequirement [1..*]'
  deft-origin: github/spec-kit@b9e08bf templates/commands/specify.md (MIT, adapted); github/spec-kit@b9e08bf templates/commands/clarify.md (MIT, adapted)
---

# Specify EARS requirements

## Inputs and outputs

- Input `request`: FeatureRequest (one)
  A change request stated by a stakeholder in natural language.
  - `text` (required)
  - `system` (optional): existing system and stack
- Output `requirements`: EARSRequirement (one or more)
  Requirement written with one of the five EARS patterns.
  - `id` (required)
  - `text` (required)
  - `source` (required): stakeholder or document the requirement comes from
  - `pattern` (required; one of ubiquitous, event-driven, state-driven, unwanted-behaviour, optional-feature)

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
<!-- deft: default section 'structure'; declared abstract by specify-requirements, implemented by ears -->

Write each requirement with exactly one EARS pattern and record which:

- Ubiquitous: `The <system> shall <response>.`
- Event-driven: `When <trigger>, the <system> shall <response>.`
- State-driven: `While <state>, the <system> shall <response>.`
- Unwanted behaviour: `If <condition>, then the <system> shall <response>.`
- Optional feature: `Where <feature is included>, the <system> shall <response>.`

Give each requirement an id `FR-<n>`.

## Validate the requirements
<!-- deft: default section 'validate'; declared by specify-requirements, overridden by ears -->

Check every requirement against this list and fix it until all items
pass (at most three iterations):

- It matches its declared EARS pattern exactly, with one `shall`.
- The trigger, state or condition is observable.
- The response is a single, testable behaviour of the named system.
- No two requirements have the same trigger and contradictory responses.

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
