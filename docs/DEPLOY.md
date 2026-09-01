# Deploy

Pick **Fly.io** or **Railway**. Same Docker image. One machine + volume is enough for Thursday.

Public URL shape: `https://<app>/mcp` for the streamable HTTP endpoint. Landing (register) is `https://<app>/`. Health: `https://<app>/health`.

Auth: paste-email → `uxmcp_` bearer. GitHub OAuth is deferred.

## Fly.io

```bash
fly auth login
fly launch --no-deploy --name open-ux --region iad
fly volumes create open_ux_data --size 1 --region iad
fly secrets set OPEN_UX_PEPPER="$(openssl rand -hex 32)"
fly secrets set OPEN_UX_PUBLIC_URL="https://open-ux.fly.dev"
fly deploy
```

`fly.toml` in the repo root points at the Dockerfile. After first deploy, set `OPEN_UX_PUBLIC_URL` to the real hostname.

## Railway

```bash
railway init
railway add  # volume mounted at /data
railway variables set OPEN_UX_PEPPER=... OPEN_UX_PUBLIC_URL=https://....up.railway.app
railway up
```

`railway.toml` uses the same Dockerfile.

## After deploy

1. Open `/` — H1 is **Open UX**.
2. Register email → copy `uxmcp_` key.
3. Client settings: URL `https://<host>/mcp` + bearer key.
4. `list_guidelines` then one `audit`. Catalog is empty until UNS-44 lands.

Self-host (no Fly/Railway): `python -m open_ux stdio` and point the client at that process. No register step.
