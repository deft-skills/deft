---
name: performance-tests
description: Use when measurable quality requirements (response time, throughput, load) must be verified with load tests.
license: GPL-3.0-only
metadata:
  deft-version: 0.1.0
  deft-lineage: generate-tests > performance-tests
  deft-inputs: 'requirements: MeasurableQualityRequirement [1..*]; code: SourceCode [1]'
  deft-outputs: 'suite: TestSuite [1]; report: TestReport [1]'
---

# Performance tests

## Inputs and outputs

- Input `requirements`: MeasurableQualityRequirement (one or more)
  Quality requirement with an objective fit criterion.
  - `id` (required)
  - `text` (required)
  - `source` (required): stakeholder or document the requirement comes from
  - `characteristic` (required): ISO/IEC 25010 product quality characteristic
  - `fitCriterion` (required): measurable condition (metric, threshold and scale) that a test can check
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
- An environment that matches production in configuration is available.

## Derive the oracle
<!-- deft: default section 'oracle'; declared abstract by generate-tests, implemented by performance-tests -->

The fit criterion is the oracle. Extract the metric (for example the 95th
percentile response time), the threshold, and the load conditions
(concurrent users, ramp-up, duration). If a fit criterion lacks any of
these, stop: the requirement is not measurable.

## Write the tests
<!-- deft: default section 'write'; declared abstract by generate-tests, implemented by performance-tests -->

Write one Locust scenario per requirement under `tests/performance/`,
reproducing the load conditions of its fit criterion. Run it headless with
a fixed duration, export the statistics, and assert the threshold on the
exported metric so that the test fails when the fit criterion is not met.

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
