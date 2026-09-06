# Privacy

Eng Done fails if any of these are violated.

- **Never persist** file contents, prompts, or raw payloads. `audit` does not take a file.
- **Keys hashed at rest.** Logs keyed by `key_hash`, never the bearer secret. Plaintext `uxmcp_` is shown once at redeem, then discarded.
- **Invite tokens hashed at rest.** One-time `inv_` tokens are stored as hashes with expiry; redeem burns them.
- **Email** is stored on the waitlist, to issue/redeem invites, and to revoke keys. No marketing mail.
- **Hosted telemetry** (purpose: improve the catalog): unique callers, tool mix, rule ids.
- **Retention ≤ 30 days.** Account delete (`POST /account/delete` with email + key) wipes keys and logs for that account.
- **Self-host stdio:** no hosted telemetry, no invite flow.

SQLite lives only on the `OPEN_UX_DATA_DIR` volume (waitlist, hashed invites, hashed keys, telemetry). It is not a dump of UI snippets. Never commit the database.
