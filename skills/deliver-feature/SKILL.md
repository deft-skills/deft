---
name: deliver-feature
description: Use when a feature request for an existing system must be specified, planned, implemented test-first and verified against its functional and quality requirements.
license: GPL-3.0-only
metadata:
  deft-version: 0.1.0
  deft-lineage: deliver-feature
  deft-inputs: 'request: FeatureRequest [1]'
  deft-outputs: 'code: SourceCode [1]; reports: TestReport [1..*]'
  deft-requires: acceptance-gherkin, execute-plan-inline, performance-tests, plan-feature, systematic-debugging, test-driven-development, user-stories, volere
---

# Deliver a feature

This skill coordinates other skills. Load each named skill when its step starts, and pass the artifacts exactly as listed. Each step is ready when all its inputs exist; steps with no dependency between them may run in any order.

## Inputs and outputs

- Input `request`: FeatureRequest (one)
  A change request stated by a stakeholder in natural language.
  - `text` (required)
  - `system` (optional): existing system and stack
- Output `code`: SourceCode (one)
  The changed code base, as a branch or a set of commits.
  - `branch` (required)
  - `commits` (one or more)
- Output `reports`: TestReport (one or more)
  Result of running a test suite against the code.
  - `verdict` (required; one of pass, fail)
  - `failures` (any number)
  - `command` (required): command that reproduces the run

## Before you start

- The feature request names the existing system and its stack.
- An environment that matches production in configuration is available.

## Workflow

### Step 1: functional

Use the skill `user-stories` (role: specify-functional).
- Input `request`: the workflow input `request`.
- Output `requirements`: UserStory.

### Step 2: quality

Use the skill `volere` (role: specify-quality).
- Input `request`: the workflow input `request`.
- Output `requirements`: VolereRequirement.

### Step 3: plan

Use the skill `plan-feature`.
- Input `requirements`: the `requirements` of step 1 (functional).
- Input `requirements`: the `requirements` of step 2 (quality).
- Output `plan`: ImplementationPlan.

### Step 4: implement

Use the skill `execute-plan-inline` (role: execute-plan).
- Input `plan`: the `plan` of step 3 (plan).
- Output `code`: SourceCode.
- While you perform this step, invoke the skill `test-driven-development` for each unit of work, and follow it completely.
- When the workflow returns here after a failure with the `diagnosis` from debug, fix only what the diagnosis identifies.

### Step 5: acceptance

Use the skill `acceptance-gherkin` (role: acceptance-tests).
- Input `requirements`: the `requirements` of step 1 (functional).
- Input `code`: the `code` of step 4 (implement).
- Output `suite`: TestSuite.
- Output `report`: TestReport.

### Step 6: performance

Use the skill `performance-tests`.
- Input `requirements`: the `requirements` of step 2 (quality).
- Input `code`: the `code` of step 4 (implement).
- Output `suite`: TestSuite.
- Output `report`: TestReport.

### Step 7: verdict (decision)

- If every report has verdict pass: finish the workflow.
- If some report has verdict fail: go to step 8 (debug).

### Step 8: debug

Use the skill `systematic-debugging`.
- Input `reports`: the `report` of step 5 (acceptance).
- Input `reports`: the `report` of step 6 (performance).
- Input `code`: the `code` of step 4 (implement).
- Output `diagnosis`: Diagnosis.

### Repair loop

- After step 8 (debug), return to step 4 (implement) and continue from there. Do this at most 3 times. If the limit is reached, stop and report the open failures instead of continuing.

## Done when

- Every requirement is covered by at least one passing test.
- The code is committed on a feature branch.
