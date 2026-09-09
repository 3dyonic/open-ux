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
_TITLE_RE = re.compile(r"<title>[^<]*</title>", re.I)
_DESC_RE = re.compile(
    r"""<meta\s+name=["']description["']\s+content="[^"]*"\s*/?>""",
    re.I,
)
_APP_RE = re.compile(r"""<div\s+id=["']app["']>\s*</div>""", re.I)


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


def _text_lines(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item]
    text = str(value).strip()
    return [text] if text else []


def _field_block(field: str, label: str, value: Any) -> str:
    items = _text_lines(value)
    if not items:
        return ""
    bodies = "".join(f'<p class="block-body">{escape(line)}</p>' for line in items)
    return (
        f'<section class="block" data-field="{escape(field, quote=True)}">'
        f"<h2>{escape(label)}</h2>{bodies}</section>"
    )


def _citations_html(guideline: dict[str, Any]) -> str:
    rows = guideline.get("citation")
    if not isinstance(rows, list):
        return ""
    items: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        source = str(row.get("source") or "").strip()
        url = str(row.get("url") or "").strip()
        if not source and not url:
            continue
        source_html = f'<p class="cite-source">{escape(source)}</p>' if source else ""
        if url.startswith("https://"):
            url_html = f'<a class="cite-url" href="{escape(url, quote=True)}">{escape(url)}</a>'
        elif url:
            url_html = f'<p class="cite-url">{escape(url)}</p>'
        else:
            url_html = ""
        items.append(f'<div class="cite-row">{source_html}{url_html}</div>')
    if not items:
        return ""
    return (
        '<section class="block" data-field="citation"><h2>Citations</h2>'
        f'<div class="cite-list">{"".join(items)}</div></section>'
    )


def render_rule_article(guideline: dict[str, Any]) -> str:
    """Visible rule body for fetchers that do not run the catalog SPA."""
    gid = str(guideline.get("id") or "")
    name = guideline_display_name(guideline)
    category = str(guideline.get("category") or "").strip()
    segment = str(guideline.get("segment") or "").strip()
    if category and segment:
        path = f"{category} / {segment}"
    else:
        path = category
    parts = [
        f'<article class="content" data-ssr-rule="{escape(gid, quote=True)}">',
        '<a class="back" href="/catalog">← Back to Catalog</a>',
    ]
    if path:
        parts.append(f'<p class="eyebrow-path">{escape(path)}</p>')
    parts.append(f'<h1 class="rule-name" data-field="name">{escape(name)}</h1>')
    if gid:
        parts.append(
            f'<p class="rule-id" data-field="id">{escape(guideline_display_id(gid))}</p>'
        )
    rule = str(guideline.get("rule") or "").strip()
    if rule:
        parts.append(f'<p class="rule-text" data-field="rule">{escape(rule)}</p>')
    parts.append(_field_block("description", "Description", guideline.get("description")))
    when = _field_block("apply_when", "When to use", guideline.get("apply_when"))
    not_when = _field_block("not_when", "Not when", guideline.get("not_when"))
    if when or not_when:
        parts.append(f'<div class="when-stack">{when}{not_when}</div>')
    parts.append(_field_block("agent_hint", "Agent hint", guideline.get("agent_hint")))
    parts.append(_field_block("pass_when", "Pass", guideline.get("pass_when")))
    parts.append(_field_block("fail_when", "Fail", guideline.get("fail_when")))
    parts.append(_citations_html(guideline))
    parts.append("</article>")
    return "".join(parts)


def _ssr(page: str, inner: str) -> str:
    return f'<div data-ssr-page="{escape(page, quote=True)}">{inner}</div>'


def _mailto(email: str) -> str:
    return f'<a href="mailto:{escape(email, quote=True)}">{escape(email)}</a>'


def render_landing_article() -> str:
    return _ssr(
        "landing",
        "<main>"
        '<p class="kicker">Cited catalog · agents audit · no vibes</p>'
        "<h1>Open UX</h1>"
        "<p>Cited UX rules agents audit against</p>"
        f"<p>{escape(LANDING_DESCRIPTION)}</p>"
        '<p><a href="/catalog">Browse catalog</a> · <a href="/invite">Request access</a></p>'
        "<h2>How it works</h2>"
        "<h3>Connect</h3>"
        "<p>Install the Claude client (or any MCP client) and paste your key.</p>"
        "<h3>List · get</h3>"
        "<p>Browse the shared catalog; every rule carries a citation.</p>"
        "<h3>Audit</h3>"
        "<p>Say the compose job; get cited criteria. The host does not take a file or return pass or fail.</p>"
        "<h2>Join the community</h2>"
        "<p>Open UX is a shared idea — cited rules anyone can fork, cite, and improve together.</p>"
        '<p><a href="https://github.com/3dyonic/open-ux">View repo</a></p>'
        "</main>",
    )


def render_catalog_index_article(guidelines: list[dict[str, Any]]) -> str:
    items: list[str] = []
    for row in guidelines:
        gid = str(row.get("id") or "")
        if not gid:
            continue
        name = guideline_display_name(row)
        rule = str(row.get("rule") or "").strip()
        href = f"/catalog/{escape(gid, quote=True)}"
        rule_html = f"<p>{escape(rule)}</p>" if rule else ""
        items.append(
            f'<a href="{href}"><span>{escape(name)}</span>{rule_html}</a>'
        )
    return _ssr(
        "catalog",
        "<main>"
        "<h1>Catalog</h1>"
        f"<p>{escape(CATALOG_DESCRIPTION)}</p>"
        f"<p>{len(items)} shown</p>"
        f'<div class="list">{"".join(items)}</div>'
        "</main>",
    )


def render_privacy_article() -> str:
    sections: list[str] = []
    for heading, paragraph, bullets in PRIVACY_SECTIONS:
        if heading == "Contact":
            body = (
                f"<p>Privacy questions: {_mailto(PRIVACY_CONTACT_EMAIL)}. "
                'To ask us to drop a catalog rule, see <a href="/sources">Sources</a>.</p>'
            )
        elif paragraph:
            body = f"<p>{escape(paragraph)}</p>"
        else:
            body = ""
        items = "".join(f"<li>{escape(item)}</li>" for item in bullets)
        list_html = f"<ul>{items}</ul>" if items else ""
        sections.append(f"<section><h2>{escape(heading)}</h2>{body}{list_html}</section>")
    return _ssr(
        "privacy",
        f"<main><h1>{escape(PRIVACY_H1)}</h1><p>{escape(PRIVACY_LEDE)}</p>"
        f"{''.join(sections)}</main>",
    )


def render_sources_article() -> str:
    sections: list[str] = []
    contact = PRIVACY_CONTACT_EMAIL
    for heading, paragraphs, bullets in SOURCES_SECTIONS:
        if heading == "Contact":
            body = (
                f"<p>Sources and catalog questions: {_mailto(contact)}. "
                'For waitlist email, keys, and analytics, see <a href="/privacy">Privacy</a>.</p>'
            )
        else:
            chunks: list[str] = []
            for item in paragraphs:
                text = escape(item).replace(escape(contact), _mailto(contact))
                chunks.append(f"<p>{text}</p>")
            body = "".join(chunks)
        items = "".join(f"<li>{escape(item)}</li>" for item in bullets)
        list_html = f"<ul>{items}</ul>" if items else ""
        closing = (
            f"<p>{escape(SOURCES_ASK_CLOSING)}</p>"
            if heading == "Ask us to change or remove a rule"
            else ""
        )
        sections.append(
            f"<section><h2>{escape(heading)}</h2>{body}{list_html}{closing}</section>"
        )
    return _ssr(
        "sources",
        f"<main><h1>{escape(SOURCES_H1)}</h1><p>{escape(SOURCES_LEDE)}</p>"
        f"{''.join(sections)}</main>",
    )


def render_health_article(payload: dict[str, Any]) -> str:
    catalog = payload.get("catalog") if isinstance(payload, dict) else None
    if not isinstance(catalog, dict):
        catalog = {}
    ok = bool(payload.get("ok")) and catalog.get("status") == "ok"
    hosted = bool(payload.get("hosted"))
    status_title = (
        "Success: host and catalog are up"
        if ok
        else "Error: catalog is not loaded"
    )
    status_body = (
        "The hosted service is running. The catalog is loaded."
        if ok
        else "The host is up. The catalog has no cited rules yet. Browse the catalog when rules land."
    )
    hosted_line = (
        "Running on the hosted service."
        if hosted
        else "Running locally, not on the hosted service."
    )
    count = catalog.get("guideline_count")
    catalog_line = f"{count} cited rules" if ok else "No cited rules loaded yet."
    return _ssr(
        "health",
        "<main>"
        f"<p>{escape(status_title)}</p>"
        f"<p>{escape(status_body)}</p>"
        "<h1>Health</h1>"
        f"<p>{escape(HEALTH_DESCRIPTION)}</p>"
        '<p><a href="/catalog">Browse catalog</a></p>'
        "<h2>Components</h2>"
        "<p>API — The service answers requests.</p>"
        f"<p>Hosted service — {escape(hosted_line)}</p>"
        f"<p>Catalog — {escape(str(catalog_line))}</p>"
        "</main>",
    )


def render_invite_article() -> str:
    return _ssr(
        "invite",
        "<main>"
        "<h1>Request access</h1>"
        f"<p>{escape(INVITE_DESCRIPTION)}</p>"
        '<form method="post" action="/invite/request">'
        '<label for="email">Email</label>'
        '<input id="email" name="email" type="email" autocomplete="email">'
        '<button type="submit">Request access</button>'
        "</form>"
        '<p><a href="/invite/redeem">Already have a token? Redeem it.</a></p>'
        "</main>",
    )


def render_requested_article() -> str:
    return _ssr(
        "requested",
        "<main>"
        "<h1>You’re on the list</h1>"
        f"<p>{escape(REQUESTED_DESCRIPTION)}</p>"
        "<p>Already have an invite? Open the link from your email to redeem.</p>"
        "</main>",
    )


def render_redeem_article() -> str:
    return _ssr(
        "redeem",
        "<main>"
        "<h1>Redeem invite</h1>"
        f"<p>{escape(REDEEM_DESCRIPTION)}</p>"
        '<form method="post" action="/invite/redeem">'
        '<label for="token">Invite token</label>'
        '<input id="token" name="token" type="text" autocomplete="off">'
        '<button type="submit">Redeem</button>'
        "</form>"
        "</main>",
    )


def render_not_found_article(guideline_id: str) -> str:
    gid = (guideline_id or "").strip() or "unknown"
    return _ssr(
        "not-found",
        "<main>"
        '<p><a href="/catalog">← Back to Catalog</a></p>'
        "<h1>Not found</h1>"
        f"<p>No guideline with id “{escape(gid)}”.</p>"
        "</main>",
    )


def _rule_head_extras(*, title: str, description: str, path: str) -> str:
    lines: list[str] = []
    for line in head_meta(title=title, description=description, path=path).splitlines():
        stripped = line.strip()
        if (
            stripped.startswith("<title>")
            or 'name="description"' in stripped
            or 'rel="icon"' in stripped
        ):
            continue
        if stripped:
            lines.append(line)
    return "\n".join(lines)


def apply_spa_shell(
    html: str,
    *,
    title: str,
    description: str,
    path: str,
    article: str,
) -> str:
    """Write page title, description, and body into the Vite shell."""
    title_e = escape(title, quote=True)
    desc_e = escape(description, quote=True)
    if _TITLE_RE.search(html):
        html = _TITLE_RE.sub(f"<title>{title_e}</title>", html, count=1)
    if _DESC_RE.search(html):
        html = _DESC_RE.sub(
            f'<meta name="description" content="{desc_e}">',
            html,
            count=1,
        )
    if 'rel="canonical"' not in html:
        extras = _rule_head_extras(title=title, description=description, path=path)
        if extras:
            if _DESC_RE.search(html):
                html = _DESC_RE.sub(
                    lambda match: f"{match.group(0)}\n{extras}",
                    html,
                    count=1,
                )
            elif "</head>" in html:
                html = html.replace("</head>", f"{extras}\n</head>", 1)
    app = f'<div id="app">{article}</div>'
    if _APP_RE.search(html):
        return _APP_RE.sub(app, html, count=1)
    if re.search(r"</body>", html, flags=re.I):
        return re.sub(r"</body>", f"{app}</body>", html, count=1, flags=re.I)
    return html + app


apply_rule_shell = apply_spa_shell


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
