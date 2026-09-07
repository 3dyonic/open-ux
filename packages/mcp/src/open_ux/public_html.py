"""Shared public HTML head, robots, sitemap, favicon, and consent/GTM helpers."""

from __future__ import annotations

import os
import re
from html import escape
from pathlib import Path
from typing import Any

CANONICAL_ORIGIN = "https://open-ux.dev"
LANDING_TITLE = "Open UX — Cited UX rules agents audit against"
LANDING_DESCRIPTION = (
    "Stop inventing UX rules from memory. Open UX is a shared, cited catalog "
    "agents list, fetch, and audit against."
)
CATALOG_TITLE = "Catalog — Open UX"
_STATIC_DIR = Path(__file__).resolve().parent / "static"
_MARK_PATH = _STATIC_DIR / "logo-mark.svg"
_FAVICON_FALLBACK = _STATIC_DIR / "favicon.svg"
FAVICON_PATH = _MARK_PATH if _MARK_PATH.is_file() else _FAVICON_FALLBACK
FAVICON_HREF = "/logo-mark.svg" if FAVICON_PATH == _MARK_PATH else "/favicon.svg"
NAV_BRAND_HTML = (
    '<a class="nav-brand" href="/">'
    f'<img class="mark" src="{FAVICON_HREF}" width="20" height="20" alt="">'
    '<span class="wordmark">Open UX</span></a>'
)
NAV_GITHUB_HTML = (
    '<a class="nav-github" href="https://github.com/3dyonic/open-ux" aria-label="GitHub">'
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16" '
    'fill="currentColor" aria-hidden="true">'
    '<path d="M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 '
    '0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 '
    '0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27'
    '-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51.56-.82 '
    '1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66'
    '-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 '
    '0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"/>'
    "</svg></a>"
)
MARK_CSS = """
    .nav-brand {
      display: flex;
      align-items: center;
      gap: 10px;
      color: inherit;
      text-decoration: none;
    }
    .mark {
      display: block;
      width: 20px;
      height: 20px;
      flex-shrink: 0;
    }
    .wordmark {
      font-size: 16px;
      font-weight: 600;
      color: var(--ink);
    }
    .nav-github {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      box-sizing: border-box;
      width: 24px;
      height: 24px;
      padding: 4px;
      color: var(--muted);
      text-decoration: none;
    }
    .nav-github svg {
      display: block;
      width: 16px;
      height: 16px;
      flex-shrink: 0;
    }
    .nav-github:hover,
    .nav-github:focus {
      color: var(--ink);
    }
"""
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
        "On public pages (home, catalog, invite request, and this privacy page) we may use Google Tag Manager and Google Analytics to understand traffic.",
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
        "Questions about privacy: use the email on your waitlist request, or contact the operator of this deployment.",
        (),
    ),
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
OSS_FOOTER_CSS = """
    .footer {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      width: 100%;
      padding: 16px 48px 24px;
      border-top: 1px solid var(--line, #DED4C8);
      background: var(--paper, #F9F6F2);
      font-size: 14px;
      line-height: 20px;
      color: var(--muted, #6A6056);
    }
    .footer p { margin: 0; }
    .footer a {
      color: var(--muted, #6A6056);
      text-decoration: underline;
    }
    .footer a:hover,
    .footer a:focus {
      color: var(--ink, #1F1B16);
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


def public_oss_footer() -> str:
    return (
        '  <footer class="footer">\n'
        "    <p>Open UX · cited UX rules agents audit against</p>\n"
        '    <p><a href="/privacy">Privacy</a></p>\n'
        "  </footer>\n"
    )


def privacy_content_html() -> str:
    parts = [
        f"    <h1>{escape(PRIVACY_H1)}</h1>\n",
        f'    <p class="lede">{escape(PRIVACY_LEDE)}</p>\n',
    ]
    for heading, paragraph, bullets in PRIVACY_SECTIONS:
        parts.append("    <section>\n")
        parts.append(f"      <h2>{escape(heading)}</h2>\n")
        if paragraph:
            parts.append(f"      <p>{escape(paragraph)}</p>\n")
        if bullets:
            parts.append("      <ul>\n")
            for item in bullets:
                parts.append(f"        <li>{escape(item)}</li>\n")
            parts.append("      </ul>\n")
        parts.append("    </section>\n")
    return "".join(parts)


def render_privacy_page(*, consent: str | None = None) -> str:
    return (
        """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
"""
        + public_gtm_head(consent)
        + head_meta(title=PRIVACY_TITLE, description=PRIVACY_DESCRIPTION, path="/privacy")
        + """
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --paper: #F9F6F2;
      --card: #ffffff;
      --ink: #1F1B16;
      --muted: #6A6056;
      --line: #DED4C8;
      --pip: #FF4B00;
      --radius: 6px;
      --sans: "IBM Plex Sans", ui-sans-serif, system-ui, sans-serif;
      --mono: "IBM Plex Mono", ui-monospace, monospace;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: var(--sans);
      line-height: 1.5;
      color: var(--ink);
      background: var(--paper);
    }
    a { color: inherit; text-decoration: none; }
    .nav {
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      padding: 16px 48px;
      background: var(--card);
      border-bottom: 1px solid var(--line);
    }
    .nav-actions {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .nav-catalog, .nav-github {
      font-size: 13px;
      font-weight: 500;
      color: var(--muted);
    }
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 10px 16px;
      border-radius: var(--radius);
      font-family: inherit;
      font-size: 14px;
      font-weight: 500;
      line-height: normal;
      cursor: pointer;
      text-decoration: none;
      border: none;
    }
    .btn--primary {
      background: var(--pip);
      color: #fff;
    }
    .btn--nav {
      padding: 8px 14px;
      font-size: 13px;
    }
    .main {
      display: flex;
      flex-direction: column;
      gap: 24px;
      width: 100%;
      max-width: 720px;
      padding: 40px 48px 48px;
    }
    h1 {
      margin: 0;
      font-size: 28px;
      font-weight: 600;
      color: var(--ink);
    }
    .lede {
      margin: 0;
      font-size: 16px;
      line-height: 24px;
      color: var(--muted);
    }
    section {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    h2 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--ink);
    }
    p, li {
      margin: 0;
      font-size: 15px;
      line-height: 22px;
      color: var(--ink);
    }
    ul {
      margin: 0;
      padding-left: 20px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
"""
        + MARK_CSS
        + CONSENT_CSS
        + OSS_FOOTER_CSS
        + """
  </style>
</head>
<body>
"""
        + public_gtm_noscript(consent)
        + """
  <header class="nav">
    """
        + NAV_BRAND_HTML
        + """
    <div class="nav-actions">
      <a class="nav-catalog" href="/catalog">Catalog</a>
      """
        + NAV_GITHUB_HTML
        + """
      <a class="btn btn--primary btn--nav" href="/invite">Get a key</a>
    </div>
  </header>
  <main class="main">
"""
        + privacy_content_html()
        + """
  </main>
"""
        + public_oss_footer()
        + public_consent_footer(consent)
        + """
</body>
</html>
"""
    )


def render_sitemap(guideline_ids: list[str]) -> str:
    locs = [canonical_url("/"), canonical_url("/catalog")]
    locs.extend(canonical_url(f"/catalog/{gid}") for gid in guideline_ids)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc in locs:
        lines.append(f"  <url><loc>{escape(loc)}</loc></url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"
