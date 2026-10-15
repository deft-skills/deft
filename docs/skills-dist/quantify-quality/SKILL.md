---
name: quantify-quality
description: Use when quality requirements without an objective metric must be made measurable before they can be tested.
license: GPL-3.0-only
metadata:
  deft-version: 0.1.0
  deft-lineage: quantify-quality
  deft-inputs: 'requirements: ISO25010Requirement [1..*]'
  deft-outputs: 'measurable: VolereRequirement [1..*]'
---

# Quantify quality requirements

## Inputs and outputs

- Input `requirements`: ISO25010Requirement (one or more)
  Quality requirement classified by ISO/IEC 25010, with an optional metric.
  - `id` (required)
  - `text` (required)
  - `source` (required): stakeholder or document the requirement comes from
  - `characteristic` (required): ISO/IEC 25010 product quality characteristic
  - `subCharacteristic` (required)
  - `metric` (optional)
- Output `measurable`: VolereRequirement (one or more)
  Volere snow card for a non-functional requirement.
  - `id` (required)
  - `text` (required)
  - `source` (required): stakeholder or document the requirement comes from
  - `characteristic` (required): ISO/IEC 25010 product quality characteristic
  - `fitCriterion` (required): measurable condition (metric, threshold and scale) that a test can check
  - `rationale` (required)
  - `type` (required): Volere requirement type number and name

## Quantify each requirement
<!-- deft: final section 'quantify'; declared by quantify-quality -->

For each input requirement:

1. Keep its id, source and characteristic.
2. Choose a metric from the ISO/IEC 25023 measures of its
   sub-characteristic (for example mean response time or throughput for
   time behaviour). If the requirement already states a metric, keep it.
3. Ask the stakeholder for the threshold and the load conditions, or
   propose them from comparable systems and mark them as assumptions.
4. Write the result as a Volere snow card whose fit criterion states the
   metric, the threshold and the conditions.

## Done when

- Every output requirement has a fit criterion with a metric, a threshold and a scale.
- Every output requirement keeps the id and source of its input requirement.
