# Diagnosis - the load run of QR-1 to QR-3 failed

Feature: `password-reset`
Reports diagnosed: `specs/password-reset/performance-report.md`, run 1
Code: branch `feature/password-reset`, commit `d4429b7`
Date: 2026-10-08

Two root causes, found one after the other: the second only became visible once
the first was removed. Neither was introduced by the password-reset feature.

## Root cause 1 - the connection was bound to the thread that created it

`sqlite3.connect()` defaults to `check_same_thread=True`, which rejects any use
of a connection from a thread other than the one that created it. FastAPI
acquires a threadpool thread **separately** for each phase of a synchronous
generator dependency, so one request's connection was created, used and closed
on up to three different threads.

### Evidence

1. The server raised `sqlite3.ProgrammingError: SQLite objects created in a
   thread can only be used in that same thread. The object was created in
   thread id 27728 and this is thread id 18564`, 9437 times in run 1, with the
   stack passing through `app/db.py:58 in get_db -> yield conn` and
   `fastapi/concurrency.py:29 in contextmanager_in_threadpool`.
2. `fastapi/concurrency.py` shows the mechanism directly: `cm.__enter__` is
   awaited through `run_in_threadpool`, the endpoint body through a second
   `run_in_threadpool` call in `fastapi/routing.py:362`, and `cm.__exit__`
   through a third `anyio.to_thread.run_sync` with its own limiter. Three
   independent thread acquisitions per request.
3. The defect is **older than this branch**. A probe against commit `d7920cb`,
   the existing system before the feature, answered 50 of 60 concurrent
   `POST /login` calls with status 500. The feature did not introduce it; the
   load test was the first thing to run the service concurrently.
4. Why the 60 functional tests never saw it: with one request at a time, anyio
   hands the same idle worker thread back, so creation and use land on the same
   thread.
5. `sqlite3.threadsafety` is 3 (serialized) on this build, so the underlying
   library permits a connection to be shared between threads; only the Python
   level check was rejecting it.

### Fix

`sqlite3.connect(path, check_same_thread=False)` in `app/db.py`. Safe here
because each request gets its own connection and its three phases run one after
another, never at the same time.

Failing test written first: `test_connection_can_be_used_from_another_thread`
and `test_connection_can_be_closed_from_another_thread` in `tests/test_db.py`,
both of which failed with the production error.

### Result

Run 2: the 95th percentile fell from 1706.8 ms to 536.3 ms and the share of
accepted requests rose from 10.44 % to 99.37 %. Still failing, which exposed the
second cause.

## Root cause 2 - writers competed for SQLite's single write lock and starved

58 requests in run 2 failed with `sqlite3.OperationalError: database is locked`,
spread across the whole run rather than clustered at start-up.

### Evidence

1. The server's own log, captured by the driver, showed
   `sqlite3.OperationalError` 58 times and nothing else.
2. Reproduced away from HTTP: 40 threads calling `issue_token` 300 times each
   produced 5 to 9 `database is locked` failures per 12 000 writes, matching the
   0.37 % seen over HTTP.
3. The traceback named the statement: the first **write** of `issue_token`,
   `DELETE FROM password_resets WHERE user_id = ?`, reached inside the deferred
   transaction that Python's `sqlite3` opens implicitly before a DML statement.
4. **Measuring the wait settled it.** Each failing call had waited 5460 ms on a
   connection whose `PRAGMA busy_timeout` read back 5000. So the busy handler
   was working and the timeout was genuinely exhausted: this was starvation
   under sustained write load, not an immediate refusal. SQLite's busy handler
   retries with a backoff that is not fair, so an unlucky writer can be
   overtaken until its timeout runs out.
5. Two cheaper hypotheses were tested and rejected by measurement, not by
   argument: `isolation_level="IMMEDIATE"` alone changed nothing (still 5
   failures per 12 000), and an explicit `BEGIN IMMEDIATE` inside `issue_token`
   only moved the error onto the `BEGIN` itself.

### Fix

`app.db.writing`, a context manager that holds a process-wide
`threading.Lock` and runs the body as one `BEGIN IMMEDIATE` transaction. Writers
then queue in the application, briefly and in order, instead of competing for
the database lock and timing out. `BEGIN IMMEDIATE` also takes the write lock up
front rather than upgrading a read, which SQLite refuses without consulting the
busy handler.

Three supporting changes, each needed by that one:

- `isolation_level=None` on the connection, so `writing` owns the transaction
  boundaries and no write begins as a deferred read.
- `password_resets.user_id` is now `UNIQUE`, so a new link replaces the
  account's previous one in a single `INSERT OR REPLACE` instead of a
  `DELETE` plus an `INSERT`. This shortens the critical section and moves
  assumption A-3 into the schema. It replaces the former non-unique index.
- PBKDF2 hashing moved outside the lock in `redeem_token` and in `register`.
  The salt is random and the hash depends on nothing in the database, so both
  are computed before the lock is taken. Hashing inside it would have throttled
  every write in the process to about 20 per second.

Failing test written first:
`test_a_slow_write_makes_the_next_writer_wait_instead_of_failing` in
`tests/test_reset.py`. It makes the first write slow and the busy timeout short,
so it fails **deterministically** with `OperationalError('database is locked')`
before the fix, rather than relying on a race.

### Known limitation

The lock spans one process. With several uvicorn workers it does not apply and
`busy_timeout` is the only backstop left, so this service runs a single worker,
which is what AQ-4 specifies. Recorded in the docstring of `writing` and in the
report.

## Result

Run 3, same conditions: 95th percentile 246.5 ms, maximum 297.9 ms, 16 442 of
16 442 requests answered 202, no 5xx, no transport error, and 16 442 e-mails for
16 442 accepted requests. All three fit criteria met.

The two earlier symptoms that were never addressed directly both disappeared as
consequences, which is what the diagnosis predicted: the latency was dominated
by error handling and lock queueing, and the surplus e-mails in runs 1 and 2
were requests the server had completed before the client gave up waiting, so
Locust recorded no status for them while the message had already been sent.
