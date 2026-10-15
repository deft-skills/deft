# Research: Formative evaluation

## Decision: mutation analysis for checkability
**Rationale**: The constraints define the faults; seeding one fault per operator at
every location tests completeness of the checker against its own specification.
**Alternatives considered**: collecting real faulty skill libraries (none exist in a
modelled form); random model fuzzing (does not map faults to constraints).
**Limitation recorded** (`experiments/README.md`): the experiment shows completeness
per constraint, not how often such faults occur in practice.

## Decision: tokens as the size unit
**Rationale**: Agents pay for what they read in tokens; lines vary with formatting.
`o200k_base` stands in for current tokenizers, because ratios between texts depend
little on the tokenizer.
**Alternatives considered**: lines only (first version), characters.

## Decision: re-model Spec Kit automatically
**Rationale**: Hand re-modelling would bias the saving. The script detects sections
repeated across commands, lifts them to an ancestor with slots for the lines that vary,
and verifies an exact round trip.
**Finding**: one copy of *Pre-Execution Checks* had drifted from the others; in the
family it becomes an explicit override.

## Decision: conventions from the pinned upstream libraries
**Rationale**: The conventions must come from practice, not from the authors' design.
14 conventions were identified in Spec Kit and Superpowers (`mapping.yaml`); two
(mixins, run-time hooks) are not covered.
