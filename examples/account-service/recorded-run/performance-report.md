# Performance test report - password reset

Feature: `password-reset`
Requirements: QR-1, QR-2, QR-3 of `specs/password-reset/requirements.md`
Date: 2026-10-08

## Suite

| File | Role |
| --- | --- |
| `tests/performance/seed.py` | registers the 1000 accounts the profile draws from |
| `tests/performance/locustfile.py` | the load profile, and the per-sample recording both windows are computed from |
| `tests/performance/run_load_test.py` | stands up one uvicorn worker on a fresh seeded database with a file outbox, drives it with Locust headless, drains and counts the outbox |
| `tests/performance/test_performance.py` | asserts the three fit criteria on one run |

One run feeds all three assertions, because the three fit criteria are defined
over the same run. Locust's own aggregate statistics could not be used directly:
QR-1 is defined over the steady-state window while QR-2 counts failures across
the ramp-up as well, so every sample is recorded and the two windows are
computed separately.

The load tests are skipped unless `--performance` is passed, so the ordinary
suite stays fast.

Reproduce with:

```
.venv/Scripts/python.exe -m pytest tests/performance -q --performance
```

## Trace

| Requirement | Test | Metric asserted |
| --- | --- | --- |
| QR-1 | `test_reset_request_p95_is_under_500_ms` | 95th percentile of the steady-state window < 500 ms |
| QR-2 | `test_reset_requests_are_accepted_under_load` | >= 99.9 % status 202, 0 responses 5xx, 0 transport errors |
| QR-3 | `test_no_reset_email_is_lost_under_load` | outbox messages == accepted requests |
| conditions of measurement | `test_the_run_met_its_own_conditions` | 200 users, 30 s ramp-up discarded, >= 66 s window, >= 10 000 samples |

Every requirement is covered.

## Verdict

**pass**, on run 3. Three runs are recorded below: the failing baseline, the
intermediate run that exposed the second cause, and the final run. The code
under test was never changed to make an assertion pass; each change came from
the diagnosis in `specs/password-reset/diagnosis.md` and was driven by a test
that failed first.

## Run 1 - baseline, before the repair

Conditions: 200 concurrent users, 1 s pacing, spawn rate 7/s (about 29 s of
ramp-up), 96 s total, 30 s of ramp-up discarded, 11 700 steady-state samples
over 65.7 s. One uvicorn worker, SQLite on local disk, 12 CPUs, load generator
co-located. Command as above.

**Verdict: fail**

| Requirement | Threshold | Measured | Result |
| --- | --- | --- | --- |
| QR-1 | p95 < 500 ms | **1706.8 ms** | fail |
| QR-2 | >= 99.9 % status 202 | **10.44 %** of 14 821 | fail |
| QR-2 | 0 responses 5xx | **9437** | fail |
| QR-2 | 0 transport errors | **3837** | fail |
| QR-3 | delivered == accepted | **1611 delivered for 1547 accepted** | fail |

Statuses over the whole run: `{"0": 3837, "202": 1547, "500": 9437}`.

Failures, one entry per failing test:

1. `test_reset_request_p95_is_under_500_ms` (QR-1) - expected a 95th percentile
   below 500 ms, measured 1706.8 ms.
2. `test_reset_requests_are_accepted_under_load` (QR-2) - expected at least
   99.9 % of requests answered 202 with no 5xx and no transport error; measured
   10.44 % accepted, 9437 responses with status 500, 3837 requests with no
   response at all.
3. `test_no_reset_email_is_lost_under_load` (QR-3) - expected one e-mail per
   accepted request; 1611 e-mails for 1547 accepted requests.

The code under test was not changed to make any assertion pass. Run 1 is
reported as measured, and the diagnosis follows in
`specs/password-reset/diagnosis.md`.

## Run 2 - after fixing the thread-bound connection

Same conditions and command. Reported because it is what exposed the second
cause.

**Verdict: fail**

| Requirement | Threshold | Measured | Result |
| --- | --- | --- | --- |
| QR-1 | p95 < 500 ms | 536.3 ms | fail |
| QR-2 | >= 99.9 % status 202 | 99.3684 % of 15 517 | fail |
| QR-2 | 0 responses 5xx | 62 | fail |
| QR-2 | 0 transport errors | 36 | fail |
| QR-3 | delivered == accepted | 15 427 for 15 419 | fail |

The remaining 500s were all `sqlite3.OperationalError`, spread over the whole
run. See the diagnosis for how they were traced to write-lock starvation.

## Run 3 - final, after both fixes

Conditions: 200 concurrent users, 1 s pacing, spawn rate 7/s, 95.4 s total,
30 s of ramp-up discarded, **13 200 steady-state samples** over 65.3 s. One
uvicorn worker, SQLite on local disk, 12 CPUs, load generator co-located.
Command as above.

**Verdict: pass**

| Requirement | Threshold | Measured | Result |
| --- | --- | --- | --- |
| QR-1 | p95 < 500 ms | **246.5 ms** | pass |
| QR-2 | >= 99.9 % status 202 | **100 %** of 16 442 | pass |
| QR-2 | 0 responses 5xx | **0** | pass |
| QR-2 | 0 transport errors | **0** | pass |
| QR-3 | delivered == accepted | **16 442 for 16 442** | pass |
| conditions | >= 10 000 samples, >= 66 s window | 13 200 samples, 65.3 s | pass |

Latency distribution of the steady-state window: median 185.9 ms, p95 246.5 ms,
p99 269.4 ms, maximum 297.9 ms. The server logged no exception of any kind.

Failures: none.

### Caveats a reader should carry

- The percentile belongs to the machine that produced it: 12 CPUs, with the
  load generator co-located, so generator and service shared the host.
- `app.db.writing` serialises writers within **one process**. The result holds
  for the single worker that AQ-4 specifies; with several uvicorn workers the
  lock does not span them and `busy_timeout` becomes the only backstop.
- The steady-state window came out at 65.3 s against the 66 s the plan aimed
  for, because the run time is counted from process start rather than from the
  first request. `test_the_run_met_its_own_conditions` allows 5 s of slack, and
  the sample count requirement of the fit criterion (10 000) is met with 13 200.
- QR-3 is counted from the file outbox, which is the mailer of the measurement
  environment. A deployment setting `APP_SMTP_HOST` is not covered by this
  measurement.

### Note on one measurement defect found and fixed before run 1

An earlier smoke run counted a transport error from Locust's `exception`
argument. Marking a response as failed through `catch_response` also makes
Locust report an exception, which conflated an HTTP 500 with a connection that
never produced a response. A transport error is now read from the absence of a
status code. This changed only the measurement, not the code under test.
