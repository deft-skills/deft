# Feature Specification: C5 review by people and LLM judges

**Feature Branch**: `008-c5-review`
**Created**: 2026-10-08
**Status**: Implemented
**Input**: "C5 cannot be decided. Record our own review of the obligations of deliver-feature, fix the gaps, and check whether independent reviewers (a second person and LLM judges) find the same gaps when they review blind."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reference review (Priority: P1)

The authors review the 8 obligations of `deliver-feature`, record verdicts and gaps in
`review.yaml`, fix the models, and review again.

**Acceptance Scenarios** (recorded in `review.yaml`):

1. Round 1: 5 of 8 obligations entailed; three gaps (acceptance: existing tests pass;
   performance: production-like environment; self: feature branch).
2. Round 2, after the fixes: 8 of 8 entailed.

### User Story 2 - Blind review by others (Priority: P1)

`items.py` rebuilds the first version of the models and lists the 16 obligations from
before and after the fixes, shuffled. A second reviewer answers in a self-contained
HTML sheet; LLM judges get the same instructions.

**Acceptance Scenarios**:

1. **Given** API keys in `.env`, **When** `judge.py` runs, **Then** answers from
   Anthropic, OpenAI and Google are cached in `results/c5_judge_cache.json`, so a rerun
   needs no keys.
2. **Given** all answers, **When** `analyse.py` runs, **Then** it reports accuracy,
   gaps found, false alarms and Cohen's kappa against the reference and pairwise.

### User Story 3 - Feed the disagreements back (Priority: P2)

Round 3 of `review.yaml` records the second reviewer and the judges. Two findings led
to fixes: all four reviewers found that `implement` could not rely on a non-empty plan
(fixed in `plan-feature`), and the second reviewer found that a "dedicated branch" is
not a feature branch (fixed in `execute-plan`). The reviewed items keep the old
conditions so the answers stay valid.

## Requirements *(mandatory)*

- **FR-001**: People and judges MUST receive the same workflow overview, definitions
  and grouped guarantees.
- **FR-002**: Rounds MUST be counterbalanced; each item carries a fingerprint.
- **FR-003**: Secrets MUST stay in `.env` (never committed); `.env.example` documents keys.

## Success Criteria *(mandatory)*

- **SC-001**: Every reviewer finds the 3 reference gaps (recorded: 3/3 for all four).
- **SC-002**: Agreement reported with kappa (recorded: 0.46–0.67 against the reference).
