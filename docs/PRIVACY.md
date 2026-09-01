# Privacy

Eng Done fails if any of these are violated.

- **Never persist** `audit.content`, prompts, or raw payloads. Store **length** and optional **content hash** only.
- **Keys hashed at rest.** Logs keyed by `key_hash`, never the bearer secret.
- **Email** is stored only to issue and revoke keys.
- **Hosted telemetry** (purpose: improve the catalog): unique callers, tool mix, audit verdicts, rule ids, target type (`html` / `jsx` / `description`).
- **Retention ≤ 30 days.** Account delete (`POST /account/delete` with email + key) wipes keys and logs for that account.
- **Self-host stdio:** no hosted telemetry.

SQLite is a local store for hosted keys + telemetry. It is not a dump of UI snippets.
