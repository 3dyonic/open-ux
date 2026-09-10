# Open UX

**Cited UX rules for agent compose and review.**

Stop inventing UX guidance from memory. This package is the shared, cited catalog plus MCP tools so an agent can find the right criteria and apply them to work it already has.

**Hosted:** [open-ux.dev](https://open-ux.dev) · **PyPI:** `open-ux` · **License:** MIT

```bash
pip install open-ux
python -m open_ux validate-catalog
python -m open_ux validate-catalog --strict-fit
python -m open_ux stdio
OPEN_UX_MODE=hosted python -m open_ux http
```

The wheel includes the catalog. `validate-catalog` and stdio work without a git checkout. `--strict-fit` gates task-language `apply_when` on four gate Leaves.

| | Hosted HTTP | Self-host (stdio) |
| -- | -- | -- |
| Auth | Waitlist → invite → bearer `uxmcp_` | None |
| Tools without a key | 401 | Allowed |
| Telemetry | Aggregated usage | Off |

Browse a local catalog site at `http://127.0.0.1:8080/catalog`. Point MCP clients at local stdio, or at hosted `/mcp` with a `uxmcp_` key.

There is no server-side LLM. `pack` returns cited criteria only — no file upload, no host pass/fail, no WCAG badge.

Tool reference (no `audit` — use `pack`): [`docs/TOOLS.md`](../../docs/TOOLS.md). Full product copy and contributing: [github.com/3dyonic/open-ux](https://github.com/3dyonic/open-ux#readme).
