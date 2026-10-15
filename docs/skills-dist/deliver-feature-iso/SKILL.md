---
name: deliver-feature-iso
description: Use when a feature request must be delivered and the organization specifies quality requirements with ISO/IEC 25010 characteristics.
license: GPL-3.0-only
metadata:
  deft-version: 0.1.0
  deft-lineage: deliver-feature-iso
  deft-inputs: 'request: FeatureRequest [1]'
  deft-outputs: 'code: SourceCode [1]; reports: TestReport [1..*]'
  deft-requires: acceptance-gherkin, execute-plan-subagents, iso25010, performance-tests, plan-feature, quantify-quality, systematic-debugging, test-driven-development, user-stories
---

# Deliver a feature (ISO/IEC 25010 quality requirements)

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

Use the skill `iso25010` (role: specify-quality).
- Input `request`: the workflow input `request`.
- Output `requirements`: ISO25010Requirement.

### Step 3: quantify

Use the skill `quantify-quality`.
- Input `requirements`: the `requirements` of step 2 (quality).
- Output `measurable`: VolereRequirement.

### Step 4: plan

Use the skill `plan-feature`.
- Input `requirements`: the `requirements` of step 1 (functional).
- Input `requirements`: the `measurable` of step 3 (quantify).
- Output `plan`: ImplementationPlan.

### Step 5: implement

Use the skill `execute-plan-subagents` (role: execute-plan).
- Input `plan`: the `plan` of step 4 (plan).
- Output `code`: SourceCode.
- While you perform this step, invoke the skill `test-driven-development` for each unit of work, and follow it completely.
- When the workflow returns here after a failure with the `diagnosis` from debug, fix only what the diagnosis identifies.

### Step 6: acceptance

Use the skill `acceptance-gherkin` (role: acceptance-tests).
- Input `requirements`: the `requirements` of step 1 (functional).
- Input `code`: the `code` of step 5 (implement).
- Output `suite`: TestSuite.
- Output `report`: TestReport.

### Step 7: performance

Use the skill `performance-tests`.
- Input `requirements`: the `measurable` of step 3 (quantify).
- Input `code`: the `code` of step 5 (implement).
- Output `suite`: TestSuite.
- Output `report`: TestReport.

### Step 8: verdict (decision)

- If every report has verdict pass: finish the workflow.
- If some report has verdict fail: go to step 9 (debug).

### Step 9: debug

Use the skill `systematic-debugging`.
- Input `reports`: the `report` of step 6 (acceptance).
- Input `reports`: the `report` of step 7 (performance).
- Input `code`: the `code` of step 5 (implement).
- Output `diagnosis`: Diagnosis.

### Repair loop

- After step 9 (debug), return to step 5 (implement) and continue from there. Do this at most 3 times. If the limit is reached, stop and report the open failures instead of continuing.

## Done when

- Every requirement is covered by at least one passing test.
- The code is committed on a feature branch.
