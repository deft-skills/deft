# Acceptance test report - password reset

Feature: `password-reset`
Code under test: branch `feature/password-reset`, commit `1eba055`
Re-verified on: commit `0a32b65`, after the two concurrency fixes of
`specs/password-reset/diagnosis.md` - 16 of 16 scenarios still pass
Date: 2026-10-08

## Verdict

**pass** - 16 of 16 scenarios passed, and the 44 tests that existed before
still pass (60 in total). Re-run on the final commit `0a32b65`: still 16 of 16,
with the suite now at 63 passed and the 4 load tests skipped by default.

Reproduce with:

```
.venv/Scripts/python.exe -m pytest tests/acceptance -q      # the 16 scenarios
.venv/Scripts/python.exe -m pytest -q                       # the whole suite
```

Failures: none.

## Suite

One `.feature` file per user story under `tests/acceptance/`, one `Scenario`
per acceptance criterion, each tagged with its story and criterion id. Step
definitions in `tests/acceptance/test_acceptance.py` go through the HTTP API
only - no step calls `app.reset` or the database. `tests/acceptance/conftest.py`
replaces the two things a scenario must control from outside: the clock the
expiry is measured against, and the e-mail transport.

| File | Story | Scenarios |
| --- | --- | --- |
| `password_reset_request.feature` | US-1 | 6 |
| `password_reset_completion.feature` | US-2 | 4 |
| `password_reset_expiry.feature` | US-3 | 3 |
| `password_reset_single_use.feature` | US-4 | 3 |

## Trace

| Requirement | Criterion | Scenario | Result |
| --- | --- | --- | --- |
| US-1 | AC-1.1 | The request is accepted | pass |
| US-1 | AC-1.2 | Exactly one link is delivered | pass |
| US-1 | AC-1.3 | An unknown address is answered the same way | pass |
| US-1 | AC-1.4 | An unknown address receives nothing | pass |
| US-1 | AC-1.5 | Requesting again delivers a different link | pass |
| US-1 | AC-1.6 | Requesting again stops the previous link working | pass |
| US-2 | AC-2.1 | A link issued a minute ago sets the new password | pass |
| US-2 | AC-2.2 | The new password logs in | pass |
| US-2 | AC-2.3 | The password used before the reset no longer logs in | pass |
| US-2 | AC-2.4 | A token the service never issued is rejected | pass |
| US-3 | AC-3.1 | Fourteen minutes is still in time | pass |
| US-3 | AC-3.2 | Sixteen minutes is too late | pass |
| US-3 | AC-3.3 | A rejected redemption leaves the password alone | pass |
| US-4 | AC-4.1 | The same link cannot be used twice | pass |
| US-4 | AC-4.2 | The password set by the first redemption still works | pass |
| US-4 | AC-4.3 | The password of the refused redemption was never set | pass |

Every input requirement is covered. No requirement is without a scenario.

Per-story counts, from `pytest tests/acceptance -m <story>`: US-1 6 passed,
US-2 4 passed, US-3 3 passed, US-4 3 passed.

## Why the result is trusted

The scenarios were written after the implementation, so passing on the first
run proves less than a test that was watched failing. Two mutations of the
production code were run to show the suite detects the behaviour it claims:

| Mutation | Scenarios that failed |
| --- | --- |
| `TOKEN_TTL_SECONDS` 900 -> 90000 | 2 (AC-3.2, AC-3.3) |
| the reset-request endpoint stops handing the message to the mailer | 12 |

`git diff app/` is empty afterwards, so the code under test is the committed
code.

## Note on the requirements

While building the trace table, the count in the summary of
`specs/password-reset/requirements.md` was found to say 19 acceptance criteria
where the stories list 16. The criteria themselves were unchanged; the count
was corrected.
