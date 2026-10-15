---
name: acceptance-playwright
description: Use when acceptance criteria must be checked through the user interface of a web application with Playwright.
license: GPL-3.0-only (includes third-party material; see LICENSE-*.txt)
metadata:
  deft-version: 0.1.0
  deft-lineage: generate-tests > acceptance-tests > acceptance-playwright
  deft-inputs: 'requirements: UserStory [1..*]; code: SourceCode [1]'
  deft-outputs: 'suite: TestSuite [1]; report: TestReport [1]'
  deft-origin: anthropics/skills@683bc88 skills/webapp-testing/SKILL.md (Apache-2.0, adapted)
---

# Acceptance tests with Playwright

## Inputs and outputs

- Input `requirements`: UserStory (one or more)
  Connextra user story with Given/When/Then acceptance criteria.
  - `id` (required)
  - `text` (required)
  - `source` (required): stakeholder or document the requirement comes from
  - `role` (required)
  - `goal` (required)
  - `benefit` (required)
  - `acceptanceCriteria` (one or more)
- Input `code`: SourceCode (one)
  The changed code base, as a branch or a set of commits.
  - `branch` (required)
  - `commits` (one or more)
- Output `suite`: TestSuite (one)
  Executable tests, each traced to the requirement ids it checks.
  - `tests` (one or more)
  - `covers` (one or more): requirement ids
- Output `report`: TestReport (one)
  Result of running a test suite against the code.
  - `verdict` (required; one of pass, fail)
  - `failures` (any number)
  - `command` (required): command that reproduces the run

## Before you start

- The code builds and its existing tests pass.

## Derive the oracle
<!-- deft: default section 'oracle'; declared abstract by generate-tests, implemented by acceptance-tests -->

Each acceptance criterion `Given <context>, when <event>, then <outcome>`
is one scenario. The context fixes the initial state, the event is the
single action under test, and the outcome is the oracle. Keep the exact
values of the criterion (durations, limits, messages).

## Write the tests
<!-- deft: default section 'write'; declared abstract by generate-tests, implemented by acceptance-playwright -->

Write one Python Playwright script per user story under
`tests/acceptance/`, one test function per acceptance criterion.

- Start the servers with `scripts/with_server.py` (run it with `--help`
  first and use it as a black box).
- Launch Chromium headless, open the page and wait for
  `networkidle` before you inspect the DOM.
- Find selectors by reconnaissance: take a screenshot or read the
  rendered content, then act with `text=`, `role=` or id selectors.
- Assert the outcome of the criterion on the rendered page, and close
  the browser at the end.

## Trace tests to requirements
<!-- deft: final section 'trace'; declared by generate-tests -->

Tag every test with the ids of the requirements it checks (for example
`@US-1` or a `covers` marker). Build a table with one row per input
requirement and the tests that cover it. A requirement without a test is
an error: write the missing test before you run the suite.

## Run and report
<!-- deft: final section 'run'; declared by generate-tests -->

Run the new tests together with the existing suite. Write the report:
verdict `pass` only if every test passed; otherwise `fail` with one entry
per failing test (test id, requirement ids, expected and actual result).
Include the exact command that reproduces the run. Do not change the code
under test to make a test pass: report the failure.

## Done when

- Every input requirement is covered by at least one test.
- The report states a verdict and the command that reproduces it.
