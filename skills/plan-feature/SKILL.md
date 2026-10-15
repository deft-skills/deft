---
name: plan-feature
description: Use when validated requirements must become an implementation plan of small, test-first tasks before any code is written.
license: GPL-3.0-only (includes third-party material; see LICENSE-*.txt)
metadata:
  deft-version: 0.1.0
  deft-lineage: plan-feature
  deft-inputs: 'requirements: Requirement [1..*]'
  deft-outputs: 'plan: ImplementationPlan [1]'
  deft-origin: github/spec-kit@b9e08bf templates/commands/plan.md (MIT, adapted); github/spec-kit@b9e08bf templates/commands/tasks.md (MIT, adapted); obra/superpowers@8ca22db skills/writing-plans/SKILL.md (MIT, adapted)
---

# Plan the feature

## Inputs and outputs

- Input `requirements`: Requirement (one or more)
  A single, uniquely identified requirement.
  - `id` (required)
  - `text` (required)
  - `source` (required): stakeholder or document the requirement comes from
- Output `plan`: ImplementationPlan (one)
  Ordered, test-first tasks that implement a set of requirements.
  - `fileStructure` (required)
  - `tasks` (one or more): each task names files, interfaces, tests and the requirement ids it covers
  - `reviewFocus` (any number)

## Before you start

- Every requirement has a unique id and is testable.

## Read the context
<!-- deft: final section 'context'; declared by plan-feature -->

Read all requirements and the project constitution, if any. Inspect the
existing code base: language, framework, test tools, and the modules the
feature touches. Record unknowns as research questions and answer each
with a decision, a rationale and the alternatives you rejected.

## Design the change
<!-- deft: final section 'design'; declared by plan-feature -->

1. Extract the entities the requirements involve, with fields, validation
   rules and state transitions, and compare them with the existing model.
2. Define the interface contracts the feature exposes (for example HTTP
   endpoints with request and response schemas).
3. Map the files to create or change and give each one responsibility.
   Follow the patterns the code base already uses.

## Write the tasks
<!-- deft: final section 'tasks'; declared by plan-feature -->

Write one task per independently testable increment, ordered by
dependency. Each task contains:

- **Files**: the exact paths to create, modify and test.
- **Interfaces**: what the task consumes from earlier tasks and what it
  produces for later ones, with exact names and types.
- **Covers**: the requirement ids the task implements.
- **Steps**, each one action with a checkable result: write the failing
  test (name and assertions with the exact values from the
  requirements), run it and see it fail, write the minimal code, run it
  and see it pass, commit.

A step is done when the implementer can write exactly one reasonable
thing from it. Do not write function bodies that the signature and the
tests already determine.

## Review the plan
<!-- deft: default section 'review'; declared by plan-feature -->

Check the plan before you hand it over:

1. Coverage: every requirement id appears in the Covers line of a task.
2. Consistency: names and types match between the tasks that produce and
   consume them.
3. Review focus: list the input classes or failure modes that no task
   tests, and add a test for each one that matters.
4. Proportion: the plan is shorter than the code it describes.

Save the plan to `specs/<feature>/plan.md`.

## Done when

- The plan has at least one task.
- Every requirement id is covered by at least one task.
- Every task names its files, its interfaces and the test that proves it.
