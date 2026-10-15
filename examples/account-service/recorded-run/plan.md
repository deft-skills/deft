# Password reset - implementation plan

Feature: `password-reset`
Requirements: `specs/password-reset/requirements.md` (US-1 to US-4, QR-1 to QR-3)
Date: 2026-10-07

## Context

Existing system: `app/main.py`, 59 lines. FastAPI app `Accounts` with `POST
/users` (201/409) and `POST /login` (200/401). SQLite via one
`sqlite3.Connection` per request from the `get_db` dependency, which also runs
`CREATE TABLE IF NOT EXISTS users` on every call. Passwords are PBKDF2-HMAC-
SHA256, 100 000 iterations, per-user hex salt. Tests: `pytest` with
`fastapi.testclient`, `pythonpath = .`, `testpaths = tests`; the `client`
fixture points `APP_DB` at `tmp_path` and reloads `app.main`.
No constitution or principles document exists in the repository.

### Research questions and decisions

**R1 - How is the e-mail handed over without spending the latency budget (QR-1)
while losing nothing (QR-3)?**
Decision: send from a FastAPI `BackgroundTasks` task, so the hand-over runs
after the response has been written, behind a `Mailer` protocol.
Rationale: QR-1 measures the client-visible exchange, which a background task
does not extend; QR-3 only requires that nothing is lost during the run, which
an in-process task after the response satisfies.
Rejected: sending inline (an SMTP round trip inside the request would dominate
the 500 ms budget); a SQLite outbox table drained by a poller (survives a
process crash, which no requirement asks for, at the cost of a worker lifecycle
and a second failure mode); Celery or Redis (no broker in this environment).

**R2 - What is stored for a token?**
Decision: store `sha256(token)` hex, never the token itself.
Rationale: a database leak then yields no usable reset link, and SHA-256 over 43
characters costs microseconds, so QR-1 is unaffected.
Rejected: storing the token verbatim (a read of the table is account takeover);
PBKDF2 over the token (would consume the whole latency budget to stretch a value
that already carries 256 bits of entropy).

**R3 - Will SQLite hold 200 writes per second without the errors QR-2 forbids?**
Decision: set `PRAGMA journal_mode=WAL`, `PRAGMA synchronous=NORMAL` and
`PRAGMA busy_timeout=5000` once per database, and create the schema once per
process instead of on every request.
Rationale: in the default rollback-journal mode, concurrent writers surface as
`sqlite3.OperationalError: database is locked`, which would appear as 5xx and
fail QR-2. WAL lets readers and one writer proceed together; `busy_timeout`
makes a writer wait instead of failing; `synchronous=NORMAL` is the usual WAL
setting and removes one fsync per transaction.
Rejected: a shared connection with `check_same_thread=False` (serialises every
request behind one lock); a connection pool (a larger change to the dependency
than the problem needs).

**R4 - How do the 14- and 16-minute cases get tested?**
Decision: a `now_epoch() -> float` seam in `app/reset.py`; tests monkeypatch it.
Rejected: `freezegun` (not installed); sleeping (a 16-minute test); inserting
rows directly from tests (couples tests to the schema).

**R5 - Keeping the single outstanding link of A-3, and single use of US-4.**
Decision: issuing deletes any earlier row for that user; redeeming claims the
row with `DELETE ... WHERE token_hash = ? AND expires_at > ?` and proceeds only
when `rowcount == 1`.
Rationale: the delete is an atomic claim, so two concurrent redemptions of one
token cannot both win; A-4 already requires unknown, expired, used and
superseded tokens to be rejected identically, so a used row carries no
information worth keeping. It also bounds the table at one row per account,
which keeps the index small under the QR-1 load.
Rejected: a `used` flag (needs its own guarded update to stay race-free and lets
the table grow with every request); a scheduled sweep of expired rows (nothing
to sweep once rows are replaced on issue and deleted on redeem).

**R6 - What actually sends the mail?**
Decision: two implementations behind one protocol. `OutboxMailer` records
messages in memory, or appends one JSON line per message to `APP_OUTBOX` when
that variable is set. `SmtpMailer` uses the standard library `smtplib` and is
selected when `APP_SMTP_HOST` is set.
Rationale: the file outbox is what QR-3 is counted from and what development
uses; `smtplib` adds no dependency, so the feature is complete without inventing
infrastructure the request never described.
Rejected: a test-only endpoint exposing the outbox (production code carrying a
test hook); an e-mail SaaS client (an unavailable dependency and credentials
this repository does not have).

**R7 - What serves the load test?**
Decision: `uvicorn`, one worker, added to `requirements.txt`; `locust` is
already a declared dependency. Verified installable in this environment on
2026-10-07.
Rejected: driving the ASGI app in-process through `httpx.ASGITransport` (it
would measure the application without a server or socket, which is not the
production configuration the precondition asks for).

## Design

### Entities

`PasswordReset` - new table `password_resets`:

| Field | Type | Rule |
| --- | --- | --- |
| `user_id` | INTEGER NOT NULL | references `users.id`; at most one row per user (A-3) |
| `token_hash` | TEXT PRIMARY KEY | `sha256(token)` hex, 64 chars (R2) |
| `expires_at` | REAL NOT NULL | `now_epoch() + 900` (US-3) |

`PRIMARY KEY (token_hash)` gives the index for the redeem lookup; a
`password_resets_user_id` index serves the delete on issue. State transitions:
*absent* -> *outstanding* on issue; *outstanding* -> *absent* on redeem, on a
new issue for the same user (A-3), or by lapsing past `expires_at`. There is no
*used* state, by R5.

`User` is unchanged; a redemption rewrites its `salt` and `password_hash` with a
freshly generated salt.

### Interface contracts

`POST /password-reset/requests`

```
request   {"email": "<EmailStr>"}
202       {"status": "accepted"}            always, registered or not (A-1)
422       pydantic error, malformed address
```

`POST /password-reset/completions`

```
request   {"token": "<str>", "new_password": "<str, min_length 1>"}
200       {"status": "reset"}
400       {"detail": "invalid or expired token"}   unknown, expired, used or superseded (A-4)
422       pydantic error, missing or empty field
```

### Files

| Path | Responsibility |
| --- | --- |
| `app/db.py` (new) | `db_path`, `connect`, `get_db`, pragmas and schema, once per database |
| `app/mailer.py` (new) | `Message`, `Mailer` protocol, `OutboxMailer`, `SmtpMailer`, `get_mailer` |
| `app/reset.py` (new) | `TOKEN_TTL_SECONDS`, `now_epoch`, `hash_token`, `issue_token`, `redeem_token` |
| `app/main.py` (change) | HTTP layer only; keeps `hash_password`, `Credentials`, `/users`, `/login`; adds the two endpoints and `reset_email_message`; `get_db` re-exported from `app.db` so `tests/test_auth.py` keeps working |
| `requirements.txt` (change) | add `uvicorn>=0.30` |
| `tests/test_db.py` (new) | pragmas, schema, env-var handling |
| `tests/test_mailer.py` (new) | memory and file outbox, SMTP wrapper, selection |
| `tests/test_reset.py` (new) | `issue_token` / `redeem_token` unit behaviour, expiry, single use, concurrency |
| `tests/test_password_reset_api.py` (new) | the two endpoints end to end |
| `perf/locustfile.py`, `perf/seed.py` (new) | the QR-1 to QR-3 load profile |

Interfaces produced, with exact signatures:

```python
# app/db.py
def db_path() -> str: ...
def connect() -> sqlite3.Connection: ...
def get_db() -> Iterator[sqlite3.Connection]: ...
def reset_schema_cache() -> None: ...

# app/mailer.py
class Message(NamedTuple):
    to: str
    subject: str
    body: str
class Mailer(Protocol):
    def send(self, message: Message) -> None: ...
class OutboxMailer:
    def __init__(self, path: str | None = None) -> None: ...
    sent: list[Message]
    def send(self, message: Message) -> None: ...
class SmtpMailer:
    def __init__(self, host: str, port: int = 25, sender: str = "no-reply@example.org") -> None: ...
    def send(self, message: Message) -> None: ...
def get_mailer() -> Mailer: ...          # cached; APP_SMTP_HOST -> SmtpMailer, else OutboxMailer(APP_OUTBOX)
def reset_mailer_cache() -> None: ...

# app/reset.py
TOKEN_TTL_SECONDS: int = 900
def now_epoch() -> float: ...
def hash_token(token: str) -> str: ...
def issue_token(conn: sqlite3.Connection, email: str) -> str | None: ...   # None when no such account
def redeem_token(conn: sqlite3.Connection, token: str, new_password: str) -> bool: ...

# app/main.py
def reset_email_message(email: str, token: str) -> Message: ...
```

`app/main.py` reads `APP_RESET_LINK_BASE` (default
`https://accounts.example.org/reset`) at call time and builds the link as
`<base>?token=<token>`, per A-7. Every module reads its environment variables at
call time, never at import, so the existing `monkeypatch.setenv` plus
`importlib.reload` fixture keeps working and the reload becomes unnecessary
rather than broken.

## Tasks

Each task: write the failing test, run it and watch it fail for the stated
reason, write the smallest code that passes, run the suite, commit.

### T1 - Database module with WAL and one-time schema

- **Files**: create `app/db.py`, `tests/test_db.py`; modify `app/main.py`.
- **Interfaces**: produces `db_path`, `connect`, `get_db`,
  `reset_schema_cache`. Consumes nothing.
- **Covers**: enabling work for QR-1 and QR-2 (no functional requirement).
- **Steps**:
  1. Test `test_connect_uses_wal_and_busy_timeout`: `PRAGMA journal_mode`
     returns `"wal"` and `PRAGMA busy_timeout` returns `5000`. Fails: no module.
  2. Test `test_schema_has_users_and_password_resets`: both table names are in
     `sqlite_master`, and `password_resets` has columns `user_id`, `token_hash`,
     `expires_at`.
  3. Test `test_db_path_follows_env_at_call_time`: setting `APP_DB` after import
     changes `db_path()`.
  4. Test `test_schema_is_created_once_per_database`: two `connect()` calls on
     one path, and `reset_schema_cache()` makes the next call initialise again.
  5. Write `app/db.py`; point `app/main.py` at it, dropping its own `DB_PATH`
     and per-request DDL and re-exporting `get_db`.
  6. Run the whole suite: `tests/test_auth.py` must still pass untouched.
  7. Commit.

### T2 - Mailer

- **Files**: create `app/mailer.py`, `tests/test_mailer.py`.
- **Interfaces**: produces `Message`, `Mailer`, `OutboxMailer`, `SmtpMailer`,
  `get_mailer`, `reset_mailer_cache`.
- **Covers**: US-1 (AC-1.2 needs something that delivers), QR-3 (the counted
  outbox).
- **Steps**:
  1. Test `test_memory_outbox_records_message`: `OutboxMailer().send(...)`
     appends to `.sent`.
  2. Test `test_file_outbox_appends_one_json_line_per_message`: two sends on
     `OutboxMailer(path=tmp)` give a 2-line file, each line a JSON object with
     `to`, `subject`, `body`.
  3. Test `test_file_outbox_is_append_safe_from_threads`: 50 threads x 10 sends
     give exactly 500 well-formed lines.
  4. Test `test_smtp_mailer_sends_through_smtplib`: a fake injected `smtplib`
     client records one `send_message` with the right `To` and `Subject`.
  5. Test `test_get_mailer_selects_by_environment`: `APP_SMTP_HOST` set gives
     `SmtpMailer`; unset gives `OutboxMailer`; the result is cached until
     `reset_mailer_cache()`.
  6. Write `app/mailer.py` (a `threading.Lock` around the file append).
  7. Commit.

### T3 - Issue a token

- **Files**: create `app/reset.py`, `tests/test_reset.py`.
- **Interfaces**: consumes `app.db.connect`. Produces `TOKEN_TTL_SECONDS`,
  `now_epoch`, `hash_token`, `issue_token`.
- **Covers**: US-1 (AC-1.5).
- **Steps**:
  1. Test `test_issue_token_returns_token_and_stores_only_its_hash`: the raw
     token does not appear in the table; `hash_token(token)` does.
  2. Test `test_issue_token_sets_expiry_15_minutes_ahead`: with `now_epoch`
     patched to `1 000 000.0`, `expires_at == 1_000_900.0`.
  3. Test `test_issue_token_returns_none_for_unknown_email`: no row is written.
  4. Test `test_issue_token_replaces_the_previous_token` (AC-1.5): two issues
     for one account give different tokens and leave exactly one row, the second
     one.
  5. Write `app/reset.py` with those four names.
  6. Commit.

### T4 - The reset-request endpoint

- **Files**: modify `app/main.py`; create `tests/test_password_reset_api.py`.
- **Interfaces**: consumes `issue_token`, `get_mailer`, `Message`. Produces
  `POST /password-reset/requests` and `reset_email_message`.
- **Covers**: US-1 (AC-1.1, AC-1.2, AC-1.3, AC-1.4).
- **Steps**:
  1. Test `test_request_for_registered_account_is_accepted` (AC-1.1): 202 and
     body `{"status": "accepted"}`.
  2. Test `test_request_for_registered_account_sends_one_link` (AC-1.2): the
     outbox holds exactly one message, addressed to `a@example.org`, whose body
     contains `?token=`.
  3. Test `test_request_for_unknown_account_looks_identical` (AC-1.3): same
     status and same body as the registered case.
  4. Test `test_request_for_unknown_account_sends_nothing` (AC-1.4): the outbox
     is empty.
  5. Test `test_malformed_address_is_rejected`: `"not-an-email"` gives 422
     (review focus).
  6. Write `ResetRequest`, the endpoint with `BackgroundTasks`, and
     `reset_email_message`.
  7. Commit.

### T5 - Redeem a token

- **Files**: modify `app/reset.py`, `app/main.py`; extend `tests/test_reset.py`,
  `tests/test_password_reset_api.py`.
- **Interfaces**: consumes `hash_password` from `app.main`, or moves it where
  both can import it without a cycle. Produces `redeem_token` and
  `POST /password-reset/completions`.
- **Covers**: US-2 (AC-2.1 to AC-2.4).
- **Steps**:
  1. Test `test_redeem_sets_the_new_password` (AC-2.1): `redeem_token` returns
     `True` and the stored hash changes, with a new salt.
  2. Test `test_completion_responds_200` (AC-2.1): a token issued one minute ago
     gives 200 and `{"status": "reset"}`.
  3. Test `test_login_with_new_password_succeeds` (AC-2.2): 200 and a token.
  4. Test `test_login_with_old_password_fails` (AC-2.3): 401.
  5. Test `test_unknown_token_is_rejected` (AC-2.4): `"not-a-real-token"` gives
     400 and `{"detail": "invalid or expired token"}`.
  6. Test `test_empty_new_password_is_rejected`: 422, per A-5 (review focus).
  7. Write `redeem_token`, `ResetCompletion` with `min_length=1`, the endpoint.
  8. Commit.

### T6 - Expiry after 15 minutes

- **Files**: extend `tests/test_reset.py`, `tests/test_password_reset_api.py`.
  Code changes only if T3 and T5 did not already satisfy the tests.
- **Interfaces**: consumes `now_epoch`, `redeem_token`.
- **Covers**: US-3 (AC-3.1, AC-3.2, AC-3.3).
- **Steps**:
  1. Test `test_token_at_14_minutes_is_accepted` (AC-3.1): issue at `t`, redeem
     at `t + 840`, 200.
  2. Test `test_token_at_16_minutes_is_rejected` (AC-3.2): redeem at `t + 960`,
     400, same detail as T5 step 5.
  3. Test `test_password_survives_an_expired_redemption` (AC-3.3): the original
     password still logs in with 200.
  4. Test `test_token_exactly_at_the_boundary_is_rejected`: `t + 900` is
     rejected, pinning the comparison to `expires_at > now` (review focus).
  5. Commit.

### T7 - Single use and superseding

- **Files**: extend `tests/test_reset.py`, `tests/test_password_reset_api.py`.
- **Interfaces**: consumes `redeem_token`, `issue_token`.
- **Covers**: US-4 (AC-4.1 to AC-4.3), US-1 (AC-1.6).
- **Steps**:
  1. Test `test_second_redemption_is_rejected` (AC-4.1): 400 with the same
     detail.
  2. Test `test_first_new_password_still_works` (AC-4.2): 200.
  3. Test `test_second_new_password_does_not_work` (AC-4.3): 401.
  4. Test `test_superseded_token_is_rejected` (AC-1.6): `L1` gives 400 after
     `L2` was issued.
  5. Test `test_concurrent_redemption_wins_once`: 8 threads redeem one token
     with 8 different passwords; exactly one `True`, and the password that logs
     in is the winner's (review focus, R5).
  6. Commit.

### T8 - Load profile for QR-1 to QR-3

Workflow step 6 runs the `performance-tests` skill, which owns the measurement.
This task exists so the plan carries the coverage and the harness is in place.

- **Files**: create `perf/locustfile.py`, `perf/seed.py`; modify
  `requirements.txt`.
- **Interfaces**: consumes the running service and `APP_OUTBOX`.
- **Covers**: QR-1, QR-2, QR-3.
- **Steps**:
  1. Add `uvicorn>=0.30` to `requirements.txt`.
  2. `perf/seed.py` registers 1000 accounts into a fresh `APP_DB`.
  3. `perf/locustfile.py`: a task that posts a reset request for a uniformly
     random seeded address, 1 s pacing, so 200 users give 200 requests per
     second (AQ-1).
  4. Run uvicorn with one worker, `APP_OUTBOX` pointed at a temp file; 30 s
     ramp, at least 60 s steady state.
  5. Assert the three fit criteria: 95th percentile below 500 ms on the
     steady-state window (QR-1); at least 99.9 % status 202 with zero 5xx and
     zero transport errors (QR-2); outbox lines equal to accepted requests after
     a drain of at most 5 s (QR-3).
  6. Record the host CPU count with the result, per AQ-4. Commit.

Workflow step 5 runs `acceptance-gherkin` over US-1 to US-4; its scenarios come
from the same acceptance criteria and need no new production code.

## Review focus

Input classes and failure modes that the tasks above now cover because this
review found them missing: a malformed e-mail address (T4 step 5); an empty new
password (T5 step 6); the exact 900-second boundary (T6 step 4); two concurrent
redemptions of one token (T7 step 5); concurrent appends to the file outbox (T2
step 3).

Known and deliberately not addressed, with the reason:

- **Timing side channel on enumeration.** The registered path writes a row, so
  it is measurably slower than the unregistered path. A-1 requires the status
  and body to match, which the tests check; equalising the timing is not
  required and would mean doing fake work on the unregistered path.
- **No rate limit on reset requests.** Nothing in the requirements asks for one,
  and a limiter would conflict with QR-2, which demands at least 99.9 % of 200
  requests per second be accepted. Worth raising with the operator separately,
  since the endpoint sends mail to third parties.
- **No audit trail of redemptions.** R5 deletes the row, so a used token leaves
  no record. No requirement asks for one.
- **E-mail address case sensitivity.** Lookup is exact, matching the existing
  behaviour of `/users` and `/login`. Unchanged by this feature.
- **Durability across a process crash.** R1 holds the pending send in memory, so
  a crash between the response and the send loses that one e-mail. QR-3 measures
  loss under load, not across a restart.
- **Outbox file growth.** The file outbox is for development and measurement; a
  deployment sets `APP_SMTP_HOST` instead.

## Coverage check

| Requirement | Task |
| --- | --- |
| US-1 (AC-1.1 to AC-1.4) | T4 |
| US-1 (AC-1.5) | T3 |
| US-1 (AC-1.6) | T7 |
| US-2 | T5 |
| US-3 | T6 |
| US-4 | T7 |
| QR-1 | T8 (enabled by T1, R1, R2) |
| QR-2 | T8 (enabled by T1) |
| QR-3 | T8 (enabled by T2) |

Consistency: `issue_token` and `redeem_token` take the connection produced by
`app.db.connect`; `reset_email_message` returns the `Message` that
`Mailer.send` accepts; `now_epoch` is the single clock used by T3, T6 and T7.
Every name in a task's Interfaces line appears in the signatures above.
