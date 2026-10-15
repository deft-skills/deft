# Feature Specification: Agent run of the example

**Feature Branch**: `006-agent-run`
**Created**: 2026-10-08
**Status**: Implemented
**Input**: "Show that the generated workflow works with a real coding agent: a small existing service, a feature request, a script to prepare a run, a script to check what the run produced, and the artifacts of one recorded run."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prepare a run (Priority: P1)

A user runs `python examples/account-service/prepare.py --dest ../deft-run` and gets
a copy of the service with the generated skills in the agent's skills folder and a
first commit.

### User Story 2 - Check a finished run (Priority: P1)

`python examples/account-service/check_run.py ../deft-run --json report.json` reports
the artifacts the skills ask for, the traceability from requirement ids (`US-`, `FR-`,
`QR-`) to tests, the feature branch, the commits made on top of the original system,
and the verdict of the test suite.

### User Story 3 - Keep one recorded run (Priority: P2)

The artifacts of one run travel with the repository in `recorded-run/`, with a table
that maps each file to its workflow step.

**Acceptance Scenarios**:

1. **Given** the recorded run, **Then** it contains requirements, plan, progress
   ledger, acceptance and performance reports, a diagnosis, the check report and a
   diff stat.
2. **Given** the performance report, **Then** it shows a failing first load run and a
   passing final run after one repair iteration (1 of 3).

## Requirements *(mandatory)*

- **FR-001**: A FastAPI + SQLite account service with pytest tests (`app/`, `tests/`).
- **FR-002**: `FEATURE-REQUEST.md`: password reset by e-mail link, 15-minute expiry,
  single use, p95 < 500 ms at 200 concurrent users.
- **FR-003**: `prepare.py` with `--dest` and `--skills-dir`.
- **FR-004**: `check_run.py` counting only commits on top of the original system.
- **FR-005**: The recorded run comes from a session with no human input after the prompt.

## Success Criteria *(mandatory)*

- **SC-001**: The recorded run's check report shows every artifact present, all 7
  requirement ids (US-1..4, QR-1..3) traced to tests, and a passing suite
  (63 passed, 4 skipped).
