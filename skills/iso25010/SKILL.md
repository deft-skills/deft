---
name: iso25010
description: Use when quality requirements must be classified by ISO/IEC 25010 characteristics and sub-characteristics.
license: GPL-3.0-only (includes third-party material; see LICENSE-*.txt)
metadata:
  deft-version: 0.1.0
  deft-lineage: specify-requirements > specify-quality > iso25010
  deft-inputs: 'request: FeatureRequest [1]'
  deft-outputs: 'requirements: ISO25010Requirement [1..*]'
  deft-origin: github/spec-kit@b9e08bf templates/commands/specify.md (MIT, adapted); github/spec-kit@b9e08bf templates/commands/clarify.md (MIT, adapted)
---

# Specify ISO/IEC 25010 requirements

## Inputs and outputs

- Input `request`: FeatureRequest (one)
  A change request stated by a stakeholder in natural language.
  - `text` (required)
  - `system` (optional): existing system and stack
- Output `requirements`: ISO25010Requirement (one or more)
  Quality requirement classified by ISO/IEC 25010, with an optional metric.
  - `id` (required)
  - `text` (required)
  - `source` (required): stakeholder or document the requirement comes from
  - `characteristic` (required): ISO/IEC 25010 product quality characteristic
  - `subCharacteristic` (required)
  - `metric` (optional)

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
<!-- deft: default section 'structure'; declared abstract by specify-requirements, implemented by iso25010 -->

Classify each quality requirement by one ISO/IEC 25010:2023 product quality
characteristic (functional suitability, performance efficiency,
compatibility, interaction capability, reliability, security,
maintainability, flexibility or safety) and one of its sub-characteristics.
Give each requirement an id `QR-<n>`. Add a metric when the stakeholder
states one; otherwise leave it empty.

## Validate the requirements
<!-- deft: default section 'validate'; declared by specify-requirements -->

Check every requirement against this list and fix it until all items
pass (at most three iterations; then record what is still open):

- It states what is needed and why, not how to build it.
- It is atomic: one need per requirement.
- It is testable: a test can pass or fail against it.
- It is unambiguous: no vague terms such as "fast", "easy" or "robust".
- It does not conflict with or duplicate another requirement.

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
- Every quality requirement names one ISO/IEC 25010 characteristic.
