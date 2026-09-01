from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from starlette.testclient import TestClient

from open_ux.server import create_mcp

ROOT = Path(__file__).resolve().parents[3]


def test_landing_h1_is_open_ux(tmp_env: Path) -> None:
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    with TestClient(app) as client:
        html = client.get("/").text
        assert "<h1>Open UX</h1>" in html
        h1 = html.split("<h1>", 1)[1].split("</h1>", 1)[0]
        assert "MCP" not in h1
        assert "Cited UX rules agents audit against" in html


def test_landing_has_figma_sections_and_register_cta(tmp_env: Path) -> None:
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    with TestClient(app) as client:
        html = client.get("/").text

    assert html.count("<h1>") == 1
    assert "@media" not in html
    assert "favicon" not in html.lower()
    assert "og:image" not in html.lower()

    assert "v1 — Forms → field labels · one catalog · no vibes" in html
    assert "Stop inventing UX rules from memory. Open UX is a shared, cited catalog agents list, fetch, and audit against." in html
    assert ">Get a key</a>" in html
    assert ">View on GitHub</a>" in html
    assert ">How it works</h2>" in html
    assert "1. Connect" in html
    assert "Install the Claude client (or any MCP client) and paste your key." in html
    assert "2. List / get" in html
    assert "Browse the shared catalog; every rule carries a citation." in html
    assert "3. Audit" in html
    assert "Send UI (html / jsx / description); get pass, fail, or incomplete with the rule id — not a guess." in html
    assert "fail · placeholder-only label" in html
    assert "pass · visible label present" in html
    assert "One open catalog. Registration gates who may call — not which rules exist." in html
    assert "Privacy: no raw audit content in logs." in html

    assert html.count('href="https://github.com/3dyonic/open-ux"') >= 2
    assert 'id="get-key"' in html
    assert 'href="/invite"' in html
    assert 'href="/register"' not in html
    assert "location.hash === '#register'" in html
    assert "location.replace('/invite')" in html
    assert 'id="reg"' not in html
    assert '<button type="submit">Register</button>' not in html
    assert "Install path:" not in html
    assert "The key is shown once." not in html
    assert "fetch('/register'" not in html
    assert "fetch('/invite/request'" not in html

    assert "--bg: #f6f8fa" in html
    assert "--paper: #ffffff" in html
    assert "--ink: #1f2328" in html
    assert "--muted: #656d76" in html
    assert "--line: #d0d7de" in html
    assert "--accent: #0969da" in html
    assert "--danger: #cf222e" in html
    assert "--danger-bg: #ffebe9" in html
    assert "--success: #1a7f37" in html
    assert "--success-bg: #dafbe1" in html


def test_invite_request_page_matches_figma(tmp_env: Path) -> None:
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    with TestClient(app) as client:
        html = client.get("/invite").text

    assert "MCP" not in html.split("<title>", 1)[1].split("</title>", 1)[0]
    assert "@media" not in html
    assert "favicon" not in html.lower()
    assert "og:image" not in html.lower()

    assert 'class="logo-mark"' in html
    assert '<span class="wordmark">Open UX</span>' in html
    assert ">GitHub</a>" in html
    assert 'href="https://github.com/3dyonic/open-ux"' in html

    assert ">Request invite</h1>" in html
    assert "Join the waitlist. We’ll email a one-time invite when approved." in html
    assert '<label for="email">Email</label>' in html
    assert 'placeholder="you@company.com"' in html
    assert '<button class="btn btn--primary" type="submit">Request invite</button>' in html
    assert "No key yet — approval issues a one-time invite link." in html
    assert "Enter a valid email to request an invite." in html
    assert "We couldn’t add you to the waitlist. Check the email and try again." in html
    assert "REQUEST ERROR" in html
    assert "card--error" in html
    assert "field__input" in html
    assert "--danger: #cf222e" in html
    assert 'fetch("/invite/request"' in html
    assert "Get a key" not in html
    assert "Email in → API key out" not in html

    assert "--bg: #f6f8fa" in html
    assert "--paper: #ffffff" in html
    assert "--ink: #1f2328" in html
    assert "--muted: #656d76" in html
    assert "--line: #d0d7de" in html
    assert "--accent: #0969da" in html
    assert "--accent-bg: #ddf4ff" in html
    assert "--radius: 6px" in html


def test_invite_requested_page_matches_figma(tmp_env: Path) -> None:
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    with TestClient(app) as client:
        html = client.get("/invite/requested").text

    assert ">You’re on the list</h1>" in html
    assert "Thanks — we’ll email a one-time invite when your request is approved." in html
    assert "Already have an invite? Open the link from your email to redeem." in html
    assert 'class="logo-mark"' in html


def test_invite_redeem_page_matches_figma(tmp_env: Path) -> None:
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    with TestClient(app) as client:
        html = client.get("/invite/redeem").text

    assert ">Redeem invite</h1>" in html
    assert "Paste your invite token, or open the link from your email." in html
    assert '<label for="token">Invite token</label>' in html
    assert 'placeholder="inv_••••••••••••"' in html
    assert '<button class="btn btn--primary" type="submit">Redeem</button>' in html
    assert "Redeeming burns the invite and mints your uxmcp_ key once." in html
    assert "Invite invalid or already used. Request a new one if needed." in html
    assert "This invite isn’t valid. It may be used, expired, or mistyped." in html
    assert "REDEEM ERROR" in html
    assert '<div class="card" id="redeem-card">' in html
    assert '<div class="card" id="success-card" hidden>' in html
    assert "card--error" in html
    assert "field__input" in html

    # First load is Redeem 16:70 only. Success 11:56 stays hidden until a minted key.
    assert 'id="success-card" hidden' in html
    assert ".card[hidden]" in html
    assert 'class="key" id="key-text"></div>' in html
    assert ">Your key</h1>" in html
    assert "Invite redeemed. Copy your key — we won’t show it in full again." in html
    assert ">Copy</button>" in html
    assert "Copy key" not in html
    assert "Back to home" not in html
    assert "Use as bearer on /mcp. Self-host stdio needs no auth." in html
    assert 'fetch("/invite/redeem"' in html
    assert "navigator.clipboard.writeText(issuedKey)" in html
    assert "hideSuccess" in html
    assert "successCard.hidden = true" in html
    assert "successCard.hidden = false" in html
    assert 'if (!res.ok || !data.key)' in html
    assert "--accent-bg: #ddf4ff" in html
    assert "--success: #1a7f37" in html


def test_plugin_title_is_open_ux() -> None:
    plugin = json.loads(
        (ROOT / "clients/claude/.claude-plugin/plugin.json").read_text(encoding="utf-8")
    )
    assert plugin["displayName"] == "Open UX"
    assert "MCP" not in plugin["displayName"]
    assert "MCP" not in plugin["name"]
    assert "MCP" not in plugin.get("description", "")


def test_readme_embeds_relative_hero() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# Open UX\n")
    assert "MCP" not in readme.split("\n", 1)[0]
    assert "![Open UX: catalog to audit flow](docs/readme-hero.svg)" in readme
    assert "[docs/LANDING.md](docs/LANDING.md)" not in readme
    assert "pip install -e \"packages/mcp[dev]\"" in readme
    assert "python -m pytest" in readme


def test_designer_landing_craft_is_not_in_the_public_repo() -> None:
    assert not (ROOT / "docs/LANDING.md").exists()


def test_readme_hero_svg_is_parseable_and_complete() -> None:
    path = ROOT / "docs/readme-hero.svg"
    raw = path.read_bytes()
    assert raw, "docs/readme-hero.svg must be committed and non-empty"
    text = raw.decode("utf-8")
    assert "Â·" not in text
    assert "forms.field_labels&" not in text
    assert 'aria-label="Open UX: catalog to audit flow"' in text
    root = ET.fromstring(text)
    assert root.tag.endswith("svg")
    assert root.get("width") == "1280"
    assert root.get("height") == "420"
    assert "Catalog" in text
    assert "Agent tools" in text
    assert "Verdict" in text
    assert "Cited UX rules agents audit against" in text
