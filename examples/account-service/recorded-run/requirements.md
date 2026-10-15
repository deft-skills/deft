# Password reset - requirements

Feature: `password-reset`
Date: 2026-10-07

Notations: functional requirements as user stories (US-n), quality
requirements as Volere snow cards (QR-n).

## Sources and stakeholders

| Source | Used for |
| --- | --- |
| `FEATURE-REQUEST.md` line 5 (stakeholder request) | US-1, US-2 |
| `FEATURE-REQUEST.md` line 6 (stakeholder request) | US-3, US-4 |
| `FEATURE-REQUEST.md` lines 7-8 (stakeholder request) | QR-1 |
| Derived by the analyst from `FEATURE-REQUEST.md` lines 5-8 | QR-2, QR-3 |
| `app/main.py` (existing system: `/users`, `/login`, SQLite, PBKDF2) | integration constraints, password handling |
| OWASP *Forgot Password* cheat sheet (industry default) | account-enumeration default, single-use and expiry handling |

Stakeholders:

- **Account holder** - a registered user who has lost access to their password.
  Primary beneficiary of US-1 to US-4 and of QR-1.
- **Attacker** - negative stakeholder. Drives the expiry, single-use and
  non-enumeration criteria.
- **Service operator** - runs the service under load. Owns QR-1 to QR-3.
- **E-mail delivery system** - external system that carries the reset link.

Key concepts:

- *Actors*: account holder, e-mail delivery system, load generator.
- *Actions*: request a reset; redeem a reset link by setting a new password.
- *Data*: e-mail address, reset token, token issue time, token used flag,
  password salt and hash.
- *Constraints*: token valid for 15 minutes from issue; token usable once;
  reset request answered in under 500 ms at the 95th percentile with 200
  concurrent users.

## Functional requirements

### US-1 - Request a reset link

- **id**: US-1
- **source**: `FEATURE-REQUEST.md` line 5 (stakeholder request)
- **role**: registered user who has forgotten their password
- **goal**: request a password-reset link to be sent to my e-mail address
- **benefit**: I can start regaining access without contacting support
- **text**: As a registered user who has forgotten their password, I want to
  request a password-reset link to be sent to my e-mail address, so that I can
  start regaining access without contacting support.
- **acceptanceCriteria**:
  - **AC-1.1**: Given a registered account for `a@example.org`, when a reset is
    requested for `a@example.org`, then the service responds with status 202.
  - **AC-1.2**: Given a registered account for `a@example.org`, when a reset is
    requested for `a@example.org`, then exactly one e-mail containing a reset
    link is delivered to `a@example.org`.
  - **AC-1.3**: Given no account exists for `ghost@example.org`, when a reset is
    requested for `ghost@example.org`, then the service responds with status 202
    and the same response body as in AC-1.1.
  - **AC-1.4**: Given no account exists for `ghost@example.org`, when a reset is
    requested for `ghost@example.org`, then no e-mail is delivered.
  - **AC-1.5**: Given a registered account for `a@example.org` with an
    outstanding reset link `L1`, when a reset is requested again for
    `a@example.org`, then a reset link `L2` different from `L1` is delivered.
  - **AC-1.6**: Given a registered account for `a@example.org` with an
    outstanding reset link `L1`, when a reset is requested again for
    `a@example.org`, then redeeming `L1` responds with status 400.

### US-2 - Set a new password through the link

- **id**: US-2
- **source**: `FEATURE-REQUEST.md` line 5 (stakeholder request)
- **role**: registered user who holds a reset link
- **goal**: set a new password through that link
- **benefit**: I can log in to my account again
- **text**: As a registered user who holds a reset link, I want to set a new
  password through that link, so that I can log in to my account again.
- **acceptanceCriteria**:
  - **AC-2.1**: Given a reset link issued 1 minute ago for `a@example.org`, when
    it is redeemed with the new password `new-pw-123456`, then the service
    responds with status 200.
  - **AC-2.2**: Given the redemption in AC-2.1 succeeded, when `a@example.org`
    logs in with `new-pw-123456`, then login responds with status 200 and a
    token.
  - **AC-2.3**: Given the redemption in AC-2.1 succeeded, when `a@example.org`
    logs in with the password used before the reset, then login responds with
    status 401.
  - **AC-2.4**: Given the token `not-a-real-token` was never issued by the
    service, when it is redeemed with the new password `new-pw-123456`, then the
    service responds with status 400.

### US-3 - Expire the link after 15 minutes

- **id**: US-3
- **source**: `FEATURE-REQUEST.md` line 6 ("expires after 15 minutes")
- **role**: account owner concerned about the security of my account
- **goal**: a reset link to stop working 15 minutes after it was issued
- **benefit**: a link that leaks or is left behind in a mailbox cannot be used
  later to take over my account
- **text**: As an account owner concerned about the security of my account, I
  want a reset link to stop working 15 minutes after it was issued, so that a
  link that leaks or is left behind in a mailbox cannot be used later to take
  over my account.
- **acceptanceCriteria**:
  - **AC-3.1**: Given a reset link for `a@example.org` issued 14 minutes ago,
    when it is redeemed with the new password `new-pw-123456`, then the service
    responds with status 200.
  - **AC-3.2**: Given a reset link for `a@example.org` issued 16 minutes ago,
    when it is redeemed with the new password `new-pw-123456`, then the service
    responds with status 400.
  - **AC-3.3**: Given the redemption in AC-3.2 was rejected, when
    `a@example.org` logs in with the password used before the reset request,
    then login responds with status 200.

### US-4 - Allow the link to be used only once

- **id**: US-4
- **source**: `FEATURE-REQUEST.md` line 6 ("can be used once")
- **role**: account owner concerned about the security of my account
- **goal**: a reset link to be refused after it has been used successfully
- **benefit**: someone who obtains the link afterwards cannot change my password
  a second time
- **text**: As an account owner concerned about the security of my account, I
  want a reset link to be refused after it has been used successfully, so that
  someone who obtains the link afterwards cannot change my password a second
  time.
- **acceptanceCriteria**:
  - **AC-4.1**: Given a reset link for `a@example.org` that was redeemed
    successfully with `new-pw-123456`, when the same link is redeemed again with
    `other-pw-123456`, then the service responds with status 400.
  - **AC-4.2**: Given the second redemption in AC-4.1 was rejected, when
    `a@example.org` logs in with `new-pw-123456`, then login responds with
    status 200.
  - **AC-4.3**: Given the second redemption in AC-4.1 was rejected, when
    `a@example.org` logs in with `other-pw-123456`, then login responds with
    status 401.

## Quality requirements

### QR-1 - Reset request latency under load

- **id**: QR-1
- **type**: 12a Speed and Latency Requirements (Volere)
- **characteristic**: Performance efficiency / Time behaviour (ISO/IEC 25010)
- **source**: `FEATURE-REQUEST.md` lines 7-8 (stakeholder request)
- **text**: The reset-request endpoint answers a password-reset request in under
  500 ms at the 95th percentile while 200 users are requesting resets
  concurrently.
- **rationale**: A user who has just discovered they cannot log in is already
  frustrated; a request that appears to hang invites repeated submissions, which
  multiply both the load and the number of live reset links. The operator needs
  the endpoint to hold this latency during an incident-driven spike, when many
  users request a reset at the same time, and not only when the service is idle.
- **fitCriterion**:
  - *Metric*: wall-clock latency of the HTTP request-response exchange for
    `POST /password-reset/requests`, recorded by the load generator.
  - *Scale*: milliseconds; the 95th percentile of all samples taken inside the
    steady-state window.
  - *Threshold*: strictly below 500 ms.
  - *Conditions of measurement*: 200 concurrent virtual users, each issuing one
    reset request per second (1 s pacing), giving a sustained target rate of 200
    requests per second; 1000 accounts seeded before the run, each request using
    an address drawn uniformly at random from those accounts; the first 30 s of
    ramp-up discarded; a steady-state window of at least 60 s, yielding at least
    10 000 samples; one service instance on the production-equivalent
    environment of the workflow precondition. The report records the host CPU
    count and the load generator's own CPU usage, because the generator is
    co-located with the service.

### QR-2 - Reset request succeeds under the same load

- **id**: QR-2
- **type**: 12c Reliability and Availability Requirements (Volere)
- **characteristic**: Reliability / Fault tolerance (ISO/IEC 25010)
- **source**: derived by the analyst from `FEATURE-REQUEST.md` lines 5-8
- **text**: While 200 users request resets concurrently, the reset-request
  endpoint keeps accepting the requests instead of rejecting or failing them.
- **rationale**: A latency target on its own can be met by a service that
  answers quickly because it is failing, so this requirement is what makes QR-1
  meaningful to the operator and to the account holder: a fast error is still a
  user locked out of their account.
- **fitCriterion**:
  - *Metric*: share of reset requests answered with status 202, and the count of
    responses with status 5xx plus transport errors (connection reset, refused
    or timed out).
  - *Scale*: percentage of samples, and an absolute count.
  - *Threshold*: at least 99.9 % answered with status 202, and exactly 0 for the
    count of 5xx responses and transport errors.
  - *Conditions of measurement*: the same run as QR-1, counted across the
    ramp-up and the steady-state window together.

### QR-3 - No reset e-mail is lost under load

- **id**: QR-3
- **type**: 12c Reliability and Availability Requirements (Volere)
- **characteristic**: Reliability / Maturity (ISO/IEC 25010)
- **source**: derived by the analyst from `FEATURE-REQUEST.md` lines 5-8
- **text**: Every reset request that the service accepts for a registered
  address results in exactly one reset e-mail, including while 200 users are
  requesting resets concurrently.
- **rationale**: The latency target in QR-1 is reached by answering before the
  e-mail has been handed over, so the hand-over happens outside the request. An
  account holder who receives no link is locked out just as surely as one whose
  request failed, and silent loss under load is invisible to the operator unless
  it is measured, so the completeness of that deferred step is itself a
  requirement.
- **fitCriterion**:
  - *Metric*: number of reset e-mails recorded in the outbox of the mailer used
    by the measurement environment, compared with the number of reset requests
    answered with status 202 for registered addresses in the same run.
  - *Scale*: ratio of recorded e-mails to accepted requests, as a percentage.
  - *Threshold*: exactly 100 % - no loss and no duplicate - read after the run
    has been allowed to drain for at most 5 s.

## Assumptions

Recorded where the request is silent; each uses an industry default.

### On the functional requirements

- **A-1 (non-enumeration)**: Requesting a reset returns the same status and body
  whether or not the address belongs to an account, so the endpoint cannot be
  used to discover which addresses are registered (OWASP default). Drives AC-1.3
  and AC-1.4.
- **A-2 (accepted response)**: The request endpoint answers 202 Accepted,
  because delivery of the e-mail completes after the response is returned (see
  QR-1 and QR-3).
- **A-3 (one outstanding link)**: Requesting a new reset invalidates any reset
  link previously issued to the same account, so at most one link per account is
  usable at a time. Drives AC-1.5 and AC-1.6.
- **A-4 (rejection is uniform)**: Unknown, expired, already-used and superseded
  tokens are all rejected with status 400 and an identical message, so a caller
  cannot tell which case applies.
- **A-5 (password rules unchanged)**: Resetting imposes the same password rules
  as registration in `app/main.py`, which applies none beyond a non-empty
  string. This feature introduces no new policy.
- **A-6 (clock)**: Expiry is measured against the server clock in UTC, from the
  moment the token is issued.
- **A-7 (link shape)**: The e-mail contains an absolute URL whose query carries
  the token; the base URL is configuration, not a requirement.
- **A-8 (no session revocation)**: `/login` returns a random bearer token that
  the service does not store, so there is no session state to revoke on reset.

### On the quality requirements

- **AQ-1 (meaning of 200 concurrent users)**: "200 concurrent users" is read as
  200 concurrent virtual users in a closed-loop load test, each pacing one reset
  request per second. Pacing is stated because an unpaced closed loop measures
  the saturation throughput of the service rather than its latency at a given
  concurrency.
- **AQ-2 (which endpoint)**: QR-1 constrains the reset-*request* endpoint only,
  as the request states. Redeeming a link is not under a latency target: it
  verifies a token and hashes a password with PBKDF2, which is deliberately
  slow, and it is not the operation that spikes during an incident.
- **AQ-3 (strict threshold)**: "under 500 ms" is a strict inequality on the 95th
  percentile, and the percentile is computed from the samples of the
  steady-state window, excluding ramp-up.
- **AQ-4 (environment)**: The production-equivalent environment of the workflow
  precondition is one service instance with its SQLite database on local disk.
  The host CPU count is recorded with each result, since a latency percentile is
  only comparable against the machine that produced it.
- **AQ-5 (registered addresses)**: The load uses registered addresses, which is
  the more expensive path, because the unregistered path does no write. This
  makes the measurement conservative.
- **AQ-6 (observed mailer)**: In the measurement environment the mailer records
  to an inspectable outbox instead of talking to a real SMTP server, so QR-3 can
  be counted and no mail is sent to real addresses during a test.

## Clarifications

None. Every point where the request was silent had a reasonable industry
default, recorded under Assumptions on 2026-10-07; no aspect met the bar of
changing scope or user experience with several equally reasonable readings and
no default.

## Validation

### Functional requirements (iteration 1 of at most 3)

- **Problem oriented** - the stories state need and benefit; HTTP status codes
  appear only in acceptance criteria, where they are the observable behaviour of
  an HTTP API.
- **Atomic** - one need per story; each criterion asserts one outcome, so the
  response, the delivery and the resulting login state are separate criteria.
- **Testable** - every criterion names concrete addresses, passwords, times and
  statuses, so it maps to one automated scenario with no further decision.
- **Unambiguous** - no vague terms; "15 minutes" and the 14/16-minute boundary
  cases replace "expires soon".
- **No conflict or duplication** - US-3 (time) and US-4 (use count) reject the
  same token for different reasons and are not reducible to each other; A-4
  keeps their responses consistent.
- **INVEST** - US-1 is independently valuable and shippable; US-2 depends on
  US-1 only for test data, not for implementation order; US-3 and US-4 are small
  additions to the redeem path and separately negotiable, as either could be
  deferred without breaking the others.

### Quality requirements (iteration 1 of at most 3)

- **Problem oriented** - QR-1 to QR-3 constrain observable behaviour at the
  endpoint and at the outbox. They name no queue, worker, index or cache; how
  the hand-over of the e-mail is deferred is left to the plan.
- **Atomic** - latency (QR-1), successful acceptance (QR-2) and completeness of
  delivery (QR-3) are three separate needs, each failing for a different reason.
- **Testable, measurable without further decisions** - each fit criterion names
  a metric, a scale, a threshold and the conditions of the run: user count,
  pacing, dataset size, ramp-up to discard, window length and sample count. A
  load test can be written from them without another choice being made.
- **Unambiguous** - "fast under load" from the request has been replaced by the
  95th percentile of a named endpoint's latency under a named load profile.
- **No conflict or duplication** - QR-2 and QR-3 are both reliability
  requirements but measure different things: QR-2 the synchronous answer, QR-3
  the deferred effect. QR-1 and QR-3 pull in opposite directions by design, and
  holding both is what forbids meeting the latency target by dropping e-mail.
- **Rationale ties the threshold to a stakeholder** - QR-1 to the account holder
  locked out during a spike and the operator carrying it, QR-2 to the user for
  whom a fast error is still a lockout, QR-3 to the user who gets no link.

Nothing is left open.

## Summary

- `specs/password-reset/requirements.md`
- User stories (functional): 4 (US-1 to US-4), with 16 acceptance criteria
  (6 for US-1, 4 for US-2, 3 for US-3, 3 for US-4).
- Volere snow cards (quality): 3 (QR-1 to QR-3), each with an ISO/IEC 25010
  characteristic and a fit criterion.
- Open clarification markers: 0.
