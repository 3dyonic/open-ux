# Privacy

Hosted Open UX never stores `audit.content`, prompts, or other UI / PII bodies. We may keep length and an optional content hash only.

**Keys and invite tokens are hashed at rest.** Logs are keyed by `key_hash`, never the bearer secret. The plaintext `uxmcp_` key is shown once at redeem, then discarded. One-time `inv_` tokens are stored as hashes with expiry; redeem burns them.

**Email** is stored for the waitlist, to issue or redeem invites, and to revoke keys. No marketing mail.

**Hosted telemetry** (to improve the shared catalog): callers (`key_hash`), tool mix, audit verdicts, rule ids, and target type (`html` / `jsx` / `description`).

**Retention is 30 days or less.** `POST /account/delete` with email and key wipes keys and logs for that account.

**Self-host stdio:** no hosted telemetry, no invite flow.

SQLite lives only on the `OPEN_UX_DATA_DIR` volume (waitlist, hashed invites, hashed keys, telemetry). It is not a dump of UI snippets. Never committed.
