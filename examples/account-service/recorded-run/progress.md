Plan: specs/password-reset/plan.md

Branch: feature/password-reset
Started: 2026-10-07

## Ledger

Task 1: complete (commits b3678a2..6b67f15, tests: `pytest` -> 7 passed)

Ruling: `SmtpMailer` takes a `client_factory` argument that the plan's signature
did not list - injecting the factory lets the wrapper be driven by a test
without a server or a global patch of the standard library - if wrong, a caller
can pass a bad factory, which the default argument makes unlikely.

Deferred (minor): `pytest` emits one pre-existing StarletteDeprecationWarning
from `fastapi/testclient.py` about httpx. It predates this branch and comes from
a dependency, not from this code.

Task 2: complete (commits 6b67f15..275b14b, tests: `pytest` -> 15 passed)

Task 3: complete (commits 275b14b..cc592b8, tests: `pytest` -> 19 passed)

Task 4: complete (commits cc592b8..242e76e, tests: `pytest` -> 24 passed)

Ruling: password hashing moved from `app/main.py` to a new `app/passwords.py`,
and `hash_token` with it - `app.reset` needs hashing and `app.main` imports
`app.reset`, so leaving it in `main` would have been an import cycle; the plan
left the choice open - if wrong, the cost is one extra module, and `app.main`
re-exports `hash_password` so nothing that imported it broke.

Ruling: `redeem_token` claims the row with `DELETE ... RETURNING user_id` rather
than a SELECT then a DELETE - one statement is the atomic claim and also yields
the account, where the two-statement form would need its own transaction to be
race-free - if wrong, it requires SQLite 3.35 or newer; this environment has
3.50.4.

Task 5: complete (commits 242e76e..4c30a8d, tests: `pytest` -> 30 passed)
  Debugged one failure: the test helper `token_from` split the link out of the
  message body but kept the following line, so the token carried trailing text.
  Fixed in the test, not the production code.

Ruling: the US-3 tests of task 6 passed without any production change, because
tasks 3 and 5 had already implemented the expiry the plan foresaw. Rather than
accept tests I never watched fail, I loosened the expiry predicate in
`redeem_token` to `expires_at > ? - 86400`, watched all four expiry tests fail
on their assertions, and restored the file - the cost if this reasoning is
wrong is that the four tests prove less than claimed, which the mutation run
rules out.

Task 6: complete (commits 4c30a8d..e3122b4, tests: `pytest` -> 36 passed)

Ruling: the task 7 tests also passed without a production change, for the same
reason - the DELETE claim of task 5 already made redemption single use, and the
DELETE on issue already superseded the previous link. Verified by two
mutations: making redemption non-consuming failed all five single-use tests
(including the eight-thread race), and removing the revoke-on-issue failed both
AC-1.6 tests. `app/reset.py` was restored and `git diff` confirms it is
unchanged.

Task 7: complete (commits e3122b4..ef50996, tests: `pytest` -> 43 passed)

Task 8 (harness only): `perf/seed.py` and `perf/locustfile.py` committed, with
`uvicorn>=0.30` added to requirements.txt. The measurement itself belongs to
workflow step 6 (the performance-tests skill), as the plan said, so the three
fit criteria are asserted there and the result is recorded with it.

Ruling: the seeder writes accounts through `app.db` instead of the HTTP API -
1000 registrations over HTTP would spend about a minute in PBKDF2 on setup that
the measurement does not cover - if wrong, the seeded rows could diverge from
what `POST /users` writes, so the seeder uses the same `app.passwords` helpers
and the same columns.

## Final review

Finding (important, fixed): an empty `token` was answered 422 by the pydantic
`min_length` check, while A-4 requires unknown, expired, used and superseded
tokens to be rejected identically with 400. An empty token is simply one the
service never issued. Fixed after watching
`test_empty_token_is_rejected_like_any_other_unusable_token` fail with
`assert 422 == 400`. `new_password` keeps `min_length=1`, which A-5 asks for.

Deferred (minor):

1. `app.db._initialised` is a plain set with no lock, so several threads can run
   `create_schema` at once on the first requests after start-up. The DDL is
   `IF NOT EXISTS` and idempotent, and `busy_timeout` covers the brief write
   lock, so the race is benign.
2. A send that raises inside the background task is lost: the client already
   has its 202 and nothing retries. No requirement asks for retry or for
   durability across a crash, and the plan recorded this under review focus.
3. The pre-existing StarletteDeprecationWarning from `fastapi/testclient.py`
   remains, as noted after task 2.

## Repair loop, iteration 1 (after the failing performance report)

Diagnosis: `specs/password-reset/diagnosis.md`. Two root causes, both older
than this branch and both exposed for the first time by the load test.

1. `sqlite3.connect` defaults to `check_same_thread=True`, but FastAPI acquires
   a threadpool thread separately for a sync dependency's setup, the endpoint
   body and the teardown. Fixed with `check_same_thread=False`. Tests written
   first: the two cross-thread tests in `tests/test_db.py`.
2. Writers competed for SQLite's single write lock and starved past
   `busy_timeout` (measured: each failure had waited 5460 ms with the timeout
   at 5000). Fixed with `app.db.writing`, a process-wide lock around one
   `BEGIN IMMEDIATE` transaction, plus `isolation_level=None`, a UNIQUE
   `user_id` so a new link replaces the old one in one statement, and PBKDF2
   moved outside the lock. Test written first:
   `test_a_slow_write_makes_the_next_writer_wait_instead_of_failing`, which
   fails deterministically rather than on a race.

Ruling: the first root cause is a defect in the pre-existing system, not in the
feature - a probe against commit d7920cb answered 50 of 60 concurrent /login
calls with 500 - and it was fixed here anyway, because QR-2 cannot be met while
it stands and the feature's own endpoint depends on the same dependency. If
wrong, the cost is one line of change to code the feature request did not name;
leaving it would have made the quality requirement unreachable.

Ruling: writes are serialised per process rather than across processes, so the
service must run one uvicorn worker. This matches AQ-4, which specifies one
instance. If wrong - that is, if the service is later scaled to several workers
- `busy_timeout` becomes the only backstop and the starvation returns; recorded
in the docstring of `writing`, in the diagnosis and in the report.

Repair loop used: 1 of at most 3.
