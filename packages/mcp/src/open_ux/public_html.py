"""Shared public HTML head, robots, sitemap, favicon, and consent/GTM helpers."""

from __future__ import annotations

import os
import re
from html import escape
from pathlib import Path
from typing import Any

from open_ux.catalog import SOURCE_HOUSES

CANONICAL_ORIGIN = "https://open-ux.dev"
LANDING_TITLE = "Open UX — Cited UX rules agents audit against"
LANDING_DESCRIPTION = (
    "Stop inventing UX rules from memory. Open UX is a shared, cited catalog "
    "agents list, fetch, and audit against."
)
CATALOG_TITLE = "Catalog — Open UX"
CATALOG_DESCRIPTION = "Cited UX rules agents audit against"
SOURCES_TITLE = "Sources — Open UX"
SOURCES_DESCRIPTION = (
    "How Open UX writes catalog rules, and how to ask us to change or remove one."
)
SOURCES_H1 = "Sources"
SOURCES_LEDE = (
    "How Open UX writes catalog rules, and how to ask us to change or remove one."
)
HEALTH_TITLE = "Health — Open UX"
HEALTH_DESCRIPTION = (
    "Whether the hosted service is up, and whether the catalog is loaded."
)
INVITE_TITLE = "Request access — Open UX"
INVITE_DESCRIPTION = (
    "Join the waitlist. We email a one-time redeem when you are approved."
)
REQUESTED_TITLE = "You’re on the list — Open UX"
REQUESTED_DESCRIPTION = (
    "Thanks — we’ll email a one-time invite when your request is approved."
)
REDEEM_TITLE = "Redeem invite — Open UX"
REDEEM_DESCRIPTION = "Paste your invite token, or open the link from your email."
NOT_FOUND_TITLE = "Not found — Open UX"
NOT_FOUND_DESCRIPTION = "This page is not here. Open the catalog to pick a rule."
NOT_FOUND_RULE_DESCRIPTION = (
    "This id is not in the catalog. Open the catalog to pick another."
)
SERVER_ERROR_TITLE = "This page could not be loaded — Open UX"
SERVER_ERROR_DESCRIPTION = "Try again in a moment."
_STATIC_DIR = Path(__file__).resolve().parent / "static"
_MARK_PATH = _STATIC_DIR / "logo-mark.svg"
_FAVICON_FALLBACK = _STATIC_DIR / "favicon.svg"
FAVICON_PATH = _MARK_PATH if _MARK_PATH.is_file() else _FAVICON_FALLBACK
FAVICON_HREF = "/logo-mark.svg" if FAVICON_PATH == _MARK_PATH else "/favicon.svg"
DEFAULT_GTM_ID = "GTM-N3BL3G9K"
CONSENT_COOKIE = "open_ux_gtm_consent"
CONSENT_GRANTED = "granted"
CONSENT_DENIED = "denied"
CONSENT_BANNER_COPY = (
    "We use cookies for analytics (Google Tag Manager / Google Analytics) "
    "to understand how the site is used."
)
PRIVACY_TITLE = "Privacy — Open UX"
PRIVACY_DESCRIPTION = (
    "How Open UX handles waitlist email, API keys, analytics, and agent "
    "usage on the hosted service."
)
PRIVACY_H1 = "Privacy"
PRIVACY_LEDE = (
    "How Open UX handles information on the hosted service at open-ux.dev."
)
# Exact PO copy for GET /privacy. Do not invent; do not render docs/PRIVACY.md.
PRIVACY_SECTIONS: tuple[tuple[str, str | None, tuple[str, ...]], ...] = (
    (
        "What this product is",
        "Open UX is a shared, cited catalog of UX rules. Agents connect with an API key. People can browse the public catalog pages and request access.",
        (),
    ),
    (
        "Analytics (this website)",
        "On public pages (home, catalog, invite request, this privacy page, and sources) we may use Google Tag Manager and Google Analytics to understand traffic.",
        (
            "These load only after you Accept the cookie banner.",
            "If you Decline, we do not load them for that choice.",
            "We do not put analytics on the agent API (/mcp) or admin tools.",
        ),
    ),
    (
        "Waitlist and API keys",
        None,
        (
            "If you request access, we store the email you give us to approve and issue an invite.",
            "After you redeem, you get an API key (uxmcp_…). We store a hash of the key, not the secret itself. The full key is shown once at redeem.",
            "Invite tokens are one-time and stored as hashes with expiry.",
        ),
    ),
    (
        "What we do not store from agent use",
        "When agents call the tools, we do not store UI files, prompts, or other raw content you send for review. Hosted logs may keep high-level usage (for example which tools ran and which rule ids were involved), keyed by a hash of your API key — not by the secret key itself.",
        (),
    ),
    (
        "Retention",
        "Hosted account and usage records are kept only as long as needed to run the service (on the order of weeks, not forever). You can ask us to delete your waitlist email and keys.",
        (),
    ),
    (
        "Self-host",
        "If you run Open UX yourself, this hosted privacy page does not apply — your process, your logs. Analytics and waitlist are hosted-only.",
        (),
    ),
    (
        "Contact",
        None,
        (),
    ),
)
PRIVACY_CONTACT_EMAIL = "contact@open-ux.dev"
SOURCES_SECTIONS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        "What a rule is",
        (
            "Each file is one claim. It has a pass/fail, and a citation that names the original page and links to it. Extra URLs on that citation are more sources for the same claim, not extra claims.",
        ),
        (),
    ),
    (
        "How we write it",
        (
            "We read published design-system and UX guidance that is already public. We write our own short pass/fail so an agent can apply the claim. We do not republish the original page.",
            "If a claim has no honest home on a Situation Card, we leave it out. Empty leaves stay empty; we do not invent criteria for them.",
        ),
        (),
    ),
    (
        "Licenses",
        (
            "Open UX (the catalog files, tools, and this site) is MIT. That license is ours. It does not cover the original design systems.",
            "The organizations we cite keep their own copyrights and licenses. Linking to them is not an endorsement, and we are not those organizations.",
        ),
        (),
    ),
    (
        "Ask us to change or remove a rule",
        (
            "If you are the source, or you believe a rule should not be in the catalog, email contact@open-ux.dev.",
            "Include:",
        ),
        (
            "the rule id (for example govuk.hide-password-by-default-show-toggle)",
            "the catalog or citation URL",
            "what you want (remove the file, drop a citation, or correct the paraphrase)",
            "who you are in relation to the source",
        ),
    ),
    ("Contact", (), ()),
)
SOURCES_ASK_CLOSING = (
    "We will look at it and reply. We may remove the file, rewrite the paraphrase, "
    "or keep it if the citation still supports the claim."
)
_GTM_ID_RE = re.compile(r"^GTM-[A-Z0-9]+$")
CONSENT_CSS = """
    .consent {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      z-index: 40;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 16px 48px;
      background: var(--card, #ffffff);
      border-top: 1px solid var(--line, #DED4C8);
      color: var(--ink, #1F1B16);
      font-size: 14px;
      line-height: 20px;
    }
    .consent[hidden] { display: none; }
    .consent-copy { margin: 0; flex: 1 1 280px; }
    .consent-copy a {
      color: var(--pip, #FF4B00);
      text-decoration: underline;
    }
    .consent-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .consent-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 8px 14px;
      border-radius: var(--radius, 6px);
      font-family: inherit;
      font-size: 14px;
      font-weight: 500;
      line-height: normal;
      cursor: pointer;
    }
    .consent-btn--accept {
      background: var(--pip, #FF4B00);
      color: #fff;
      border: none;
    }
    .consent-btn--decline {
      background: transparent;
      color: var(--ink, #1F1B16);
      border: 1px solid var(--ink, #1F1B16);
    }
"""
PAGE_SHELL_CSS = """
    body {
      min-height: 100vh;
      min-height: 100dvh;
      display: flex;
      flex-direction: column;
    }
    main {
      flex: 1;
    }
"""
ROBOTS_TXT = """User-agent: *
Allow: /
Allow: /catalog
Allow: /catalog/
Disallow: /mcp
Disallow: /admin
Disallow: /invite/redeem
Disallow: /account

Sitemap: https://open-ux.dev/sitemap.xml
"""


def canonical_url(path: str) -> str:
    text = path if path.startswith("/") else f"/{path}"
    if text != "/" and text.endswith("/"):
        text = text.rstrip("/")
    return f"{CANONICAL_ORIGIN}{text}"


def _short_description(text: str, limit: int = 155) -> str:
    raw = " ".join(text.split()).strip()
    if not raw:
        return ""
    for sep in (". ", ".\n"):
        if sep in raw:
            raw = raw.split(sep, 1)[0].strip()
            break
    if raw and raw[-1] not in ".!?":
        raw += "."
    if len(raw) <= limit:
        return raw
    cut = raw[: limit - 1].rsplit(" ", 1)[0].rstrip(".,;:")
    return f"{cut}…"


def rule_meta_description(guideline: dict[str, Any]) -> str:
    for key in ("rule", "description"):
        text = _short_description(str(guideline.get(key) or ""))
        if text:
            return text
    return LANDING_DESCRIPTION


def rule_meta_title(display_name: str) -> str:
    name = (display_name or "").strip() or "Catalog"
    return f"{name} — Open UX"


_HOUSE_SUFFIXES = tuple(
    sorted((f" — {label}" for label in SOURCE_HOUSES.values()), key=len, reverse=True)
)


def guideline_display_name(guideline: dict[str, Any]) -> str:
    raw = str(
        guideline.get("name") or guideline.get("title") or guideline.get("id") or ""
    ).strip()
    for suffix in _HOUSE_SUFFIXES:
        if raw.endswith(suffix):
            return raw[: -len(suffix)].rstrip()
    return raw


def guideline_display_id(guideline_id: str) -> str:
    text = (guideline_id or "").strip()
    if "." not in text:
        return text
    lane, rest = text.split(".", 1)
    if rest and lane in SOURCE_HOUSES:
        return rest
    return text


def head_meta(*, title: str, description: str, path: str) -> str:
    url = canonical_url(path)
    title_e = escape(title, quote=True)
    desc_e = escape(description, quote=True)
    url_e = escape(url, quote=True)
    return (
        f"  <title>{title_e}</title>\n"
        f'  <meta name="description" content="{desc_e}">\n'
        f'  <link rel="canonical" href="{url_e}">\n'
        f'  <meta property="og:site_name" content="Open UX">\n'
        f'  <meta property="og:title" content="{title_e}">\n'
        f'  <meta property="og:description" content="{desc_e}">\n'
        f'  <meta property="og:url" content="{url_e}">\n'
        f'  <meta property="og:type" content="website">\n'
        '  <meta name="twitter:card" content="summary">\n'
        f'  <meta name="twitter:title" content="{title_e}">\n'
        f'  <meta name="twitter:description" content="{desc_e}">\n'
        f'  <link rel="icon" href="{FAVICON_HREF}" type="image/svg+xml">'
    )


def gtm_container_id() -> str:
    raw = os.environ.get("OPEN_UX_GTM_ID", "").strip()
    if raw and _GTM_ID_RE.fullmatch(raw):
        return raw
    return DEFAULT_GTM_ID


def consent_state(value: str | None) -> str:
    raw = (value or "").strip()
    if raw in {CONSENT_GRANTED, CONSENT_DENIED}:
        return raw
    return ""


def consent_granted(value: str | None) -> bool:
    return consent_state(value) == CONSENT_GRANTED


def gtm_head_html(container_id: str | None = None) -> str:
    cid = escape(container_id or gtm_container_id(), quote=True)
    return (
        "  <script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':\n"
        "new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],\n"
        "j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=\n"
        "'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);\n"
        f"}})(window,document,'script','dataLayer','{cid}');</script>\n"
    )


def gtm_noscript_html(container_id: str | None = None) -> str:
    cid = escape(container_id or gtm_container_id(), quote=True)
    return (
        '  <noscript><iframe src="https://www.googletagmanager.com/ns.html?id='
        f'{cid}" height="0" width="0" style="display:none;visibility:hidden">'
        "</iframe></noscript>\n"
    )


def public_gtm_head(consent: str | None) -> str:
    if not consent_granted(consent):
        return ""
    return gtm_head_html()


def public_gtm_noscript(consent: str | None) -> str:
    if not consent_granted(consent):
        return ""
    return gtm_noscript_html()


def consent_banner_html(*, hidden: bool = False) -> str:
    hidden_attr = " hidden" if hidden else ""
    return (
        f'  <div class="consent" id="consent-banner"{hidden_attr}>\n'
        f'    <p class="consent-copy">{escape(CONSENT_BANNER_COPY)} '
        f'<a href="/privacy">Privacy</a></p>\n'
        '    <div class="consent-actions">\n'
        '      <button type="button" class="consent-btn consent-btn--accept" '
        'id="consent-accept">Accept</button>\n'
        '      <button type="button" class="consent-btn consent-btn--decline" '
        'id="consent-decline">Decline</button>\n'
        "    </div>\n"
        "  </div>\n"
    )


def consent_script_html() -> str:
    key = CONSENT_COOKIE
    granted = CONSENT_GRANTED
    denied = CONSENT_DENIED
    return f"""  <script>
    (function () {{
      var KEY = "{key}";
      var banner = document.getElementById("consent-banner");
      function readFlag() {{
        try {{
          var ls = localStorage.getItem(KEY);
          if (ls === "{granted}" || ls === "{denied}") return ls;
        }} catch (e) {{}}
        var m = document.cookie.match(new RegExp("(?:^|; )" + KEY + "=([^;]*)"));
        return m ? decodeURIComponent(m[1]) : "";
      }}
      function writeFlag(value) {{
        document.cookie = KEY + "=" + value + "; path=/; SameSite=Lax";
        try {{ localStorage.setItem(KEY, value); }} catch (e) {{}}
      }}
      var flag = readFlag();
      if (flag === "{granted}" || flag === "{denied}") {{
        if (banner) banner.hidden = true;
        return;
      }}
      if (banner) banner.hidden = false;
      var accept = document.getElementById("consent-accept");
      var decline = document.getElementById("consent-decline");
      if (accept) accept.addEventListener("click", function () {{
        writeFlag("{granted}");
        location.reload();
      }});
      if (decline) decline.addEventListener("click", function () {{
        writeFlag("{denied}");
        if (banner) banner.hidden = true;
      }});
    }})();
  </script>
"""


def public_consent_footer(consent: str | None = None) -> str:
    decided = bool(consent_state(consent))
    return consent_banner_html(hidden=decided) + consent_script_html()


def render_sitemap(guideline_ids: list[str]) -> str:
    locs = [
        canonical_url("/"),
        canonical_url("/catalog"),
        canonical_url("/privacy"),
        canonical_url("/sources"),
    ]
    locs.extend(canonical_url(f"/catalog/{gid}") for gid in guideline_ids)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc in locs:
        lines.append(f"  <url><loc>{escape(loc)}</loc></url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"
