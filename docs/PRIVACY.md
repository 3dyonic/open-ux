# Privacy

Eng Done fails if any of these are violated.

- **Never persist** file contents, prompts, or raw payloads. `audit` does not take a file.
- **Keys hashed at rest.** Logs keyed by `key_hash`, never the bearer secret. Plaintext `uxmcp_` is shown once at redeem, then discarded.
- **Invite tokens hashed at rest.** One-time `inv_` tokens are stored as hashes with expiry; redeem burns them.
- **Email** is stored on the waitlist, to issue/redeem invites, and to revoke keys. No marketing mail.
- **Hosted telemetry** (purpose: improve the catalog): unique callers, tool mix, rule ids.
- **Retention ≤ 30 days.** Account delete (`POST /account/delete` with email + key) wipes keys and logs for that account.
- **Self-host stdio:** no hosted telemetry, no invite flow.
- **Public analytics (after consent):** Public pages (`/`, `/catalog`, `/catalog/{id}`, `/invite`, `/privacy`, `/sources`) load Google Tag Manager and Google Analytics only after you Accept the cookie banner. Decline keeps analytics off for that choice. Cookie settings in the footer opens the banner again. The consent cookie is `open_ux_gtm_consent`. The container id comes from `OPEN_UX_GTM_ID` (default `GTM-N3BL3G9K`). No analytics on `/mcp`, `/admin`, `/invite/redeem`, `/account`, or `/health`.

SQLite lives only on the `OPEN_UX_DATA_DIR` volume (waitlist, hashed invites, hashed keys, telemetry). It is not a dump of UI snippets. Never commit the database.
