Use the skill `deliver-feature` for this feature request.

**System.** The account service in this repository (FastAPI, SQLite, pytest).

**Feature request.** Users who forgot their password can reset it through a
link sent by e-mail. The link expires after 15 minutes and can be used once.
Requesting a reset must stay fast under load: the reset request responds in
under 500 ms at the 95th percentile with 200 concurrent users.
