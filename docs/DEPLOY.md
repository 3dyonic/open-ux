# Deploy

Pick **Fly.io** or **Railway**. Same Docker image. One machine + volume is enough for Thursday.

Public URL shape: `https://<app>/mcp` for the streamable HTTP endpoint. Landing is `https://<app>/`. Invite request is `https://<app>/invite`. Health: `https://<app>/health`.

Auth: waitlist email → admin approve → redeem one-time invite → `uxmcp_` bearer. GitHub OAuth is deferred. Admin UI is out; list waitlist via `GET /admin/invite/waitlist`; approve via CLI or `POST /admin/invite/approve`.

Secrets (all required for hosted invite):

- `OPEN_UX_PEPPER` — hashes keys and invite tokens
- `OPEN_UX_ADMIN_TOKEN` — bearer for `GET /admin/invite/waitlist` and `POST /admin/invite/approve`
- `OPEN_UX_PUBLIC_URL` — origin used in redeem URLs returned to the PO

SQLite is created under `OPEN_UX_DATA_DIR` (Fly/Railway volume `/data`). Never commit it.

## Fly.io

```bash
fly auth login
fly launch --no-deploy --name open-ux --region iad
fly volumes create open_ux_data --size 1 --region iad
fly secrets set OPEN_UX_PEPPER="$(openssl rand -hex 32)"
fly secrets set OPEN_UX_ADMIN_TOKEN="$(openssl rand -hex 32)"
fly secrets set OPEN_UX_PUBLIC_URL="https://open-ux.fly.dev"
fly deploy
```

`fly.toml` in the repo root points at the Dockerfile. After first deploy, set `OPEN_UX_PUBLIC_URL` to the real hostname.

## Railway

```bash
railway init
railway add  # volume mounted at /data
railway variables set OPEN_UX_PEPPER=... OPEN_UX_ADMIN_TOKEN=... OPEN_UX_PUBLIC_URL=https://....up.railway.app
railway up
```

`railway.toml` uses the same Dockerfile.

## After deploy

1. Open `/` — H1 is **Open UX**. **Get a key** goes to `/invite`.
2. Request invite with email (waitlist). `#register` and `/register` redirect into `/invite`.
3. List the waitlist (Operator notify; email + `created_at` only, newest first). Approve stays POST only — do not auto-approve:

```bash
curl -sS "$OPEN_UX_PUBLIC_URL/admin/invite/waitlist" \
  -H "Authorization: Bearer $OPEN_UX_ADMIN_TOKEN"
```

```bash
python -m open_ux approve-invite user@company.com
```

```bash
curl -sS -X POST "$OPEN_UX_PUBLIC_URL/admin/invite/approve" \
  -H "Authorization: Bearer $OPEN_UX_ADMIN_TOKEN" \
  -H "content-type: application/json" \
  -d '{"email":"user@company.com"}'
```

4. Recipient opens the redeem URL (or pastes `inv_…` on `/invite/redeem`) → copy `uxmcp_` key once.
5. Client settings: URL `https://<host>/mcp` + bearer key.
6. `list_guidelines` (paged index) then one scoped `audit` (`jobs` or `guideline_ids`).

Self-host (no Fly/Railway): `python -m open_ux stdio` and point the client at that process. No invite step.
