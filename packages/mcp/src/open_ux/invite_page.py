"""Hosted invite HTML modules: F3 Request / Requested / Redeem / Success / Error.

Frames: Request 13:9, Requested 13:37, Redeem 13:55, Success 13:78, Error 13:99.
Request is email-only — do not add Full name. Admin is CLI-only — not in this page.
"""

from __future__ import annotations

_CSS = """
    :root {
      --paper: #F9F6F2;
      --card: #ffffff;
      --ink: #1F1B16;
      --muted: #6A6056;
      --line: #DED4C8;
      --pip: #FF4B00;
      --pip-soft: #FFECE0;
      --danger: #B82A2A;
      --success: #1A7F37;
      --radius: 6px;
      --sans: "IBM Plex Sans", ui-sans-serif, system-ui, sans-serif;
      --mono: "IBM Plex Mono", ui-monospace, monospace;
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      font-family: var(--sans);
      line-height: 1.5;
      color: var(--ink);
      background: var(--paper);
    }
    a { color: inherit; }
    .pip {
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--pip);
      flex-shrink: 0;
    }
    .nav {
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      padding: 16px 48px;
      background: var(--card);
      border-bottom: 1px solid var(--line);
    }
    .nav-brand {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .wordmark {
      font-size: 16px;
      font-weight: 600;
      color: var(--ink);
    }
    .nav-actions {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .nav-github {
      font-size: 13px;
      font-weight: 500;
      color: var(--muted);
      text-decoration: none;
    }
    .main {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 48px 48px 56px;
    }
    .card {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 16px;
      width: 480px;
      max-width: 100%;
      padding: 32px;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: var(--radius);
    }
    .card[hidden] {
      display: none;
    }
    .meta {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0;
      font-family: var(--mono);
      font-size: 11px;
      font-weight: 400;
      color: var(--muted);
    }
    .kicker {
      display: none;
      align-items: center;
      gap: 8px;
      margin: 0;
      font-family: var(--mono);
      font-size: 11px;
      font-weight: 500;
      color: var(--danger);
    }
    .kicker .pip { background: var(--danger); }
    .card--error {
      border-color: var(--danger);
    }
    .card--error .meta {
      display: none;
    }
    .card--error .kicker {
      display: flex;
    }
    .card--error label {
      color: var(--danger);
    }
    .card--error .sub {
      color: var(--danger);
    }
    .card--error .field__input {
      border-color: var(--danger);
    }
    .title {
      margin: 0;
      font-size: 28px;
      font-weight: 600;
      line-height: 34px;
      color: var(--ink);
    }
    .sub {
      margin: 0;
      font-size: 14px;
      font-weight: 400;
      line-height: 20px;
      color: var(--muted);
    }
    form {
      display: contents;
    }
    .field {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 6px;
      width: 100%;
    }
    label {
      font-size: 12px;
      font-weight: 500;
      color: var(--ink);
    }
    .field__input {
      width: 100%;
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--card);
      color: var(--ink);
      font-family: inherit;
      font-size: 14px;
    }
    .field__input::placeholder {
      color: var(--muted);
    }
    .helper {
      display: none;
      margin: 0;
      font-size: 13px;
      font-weight: 400;
      line-height: 18px;
      color: var(--danger);
    }
    .helper.is-visible {
      display: block;
    }
    .link {
      margin: 0;
      font-size: 13px;
      font-weight: 500;
      color: var(--pip);
      text-decoration: none;
    }
    .foot {
      margin: 0;
      font-size: 12px;
      font-weight: 400;
      color: var(--muted);
    }
    .foot--meta {
      font-family: var(--mono);
      font-size: 11px;
    }
    .foot--exclusive {
      display: none;
      font-family: var(--mono);
      font-size: 11px;
      color: var(--muted);
    }
    .card--error .foot--exclusive {
      display: block;
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
    }
    .btn--primary {
      background: var(--pip);
      color: #fff;
      border: none;
    }
    .btn--nav {
      padding: 8px 14px;
      font-size: 13px;
    }
    .key {
      width: 100%;
      padding: 12px;
      background: var(--pip-soft);
      border: 1px solid var(--pip);
      border-radius: var(--radius);
      font-family: var(--mono);
      font-size: 14px;
      font-weight: 500;
      color: var(--pip);
    }
"""

_NAV = """
  <header class="nav">
    <div class="nav-brand">
      <span class="pip" aria-hidden="true"></span>
      <span class="wordmark">Open UX</span>
    </div>
    <div class="nav-actions">
      <a class="nav-github" href="https://github.com/3dyonic/open-ux">GitHub</a>
      <a class="btn btn--primary btn--nav" href="/invite">Get a key</a>
    </div>
  </header>
"""


def _page(main: str, script: str) -> str:
    return (
        """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Open UX</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
"""
        + _CSS
        + """
  </style>
</head>
<body>
"""
        + _NAV
        + """
  <main class="main">
"""
        + main
        + """
  </main>
  <script>
"""
        + script
        + """
  </script>
</body>
</html>
"""
    )


REQUEST_HTML = _page(
    """
    <div class="card" id="request-card">
      <p class="meta"><span class="pip" aria-hidden="true"></span>Invite · waitlist, one key after approve</p>
      <p class="kicker" id="request-error-kicker"><span class="pip" aria-hidden="true"></span>REQUEST ERROR</p>
      <h1 class="title">Request access</h1>
      <p class="sub" id="request-sub">Join the waitlist. We email a one-time redeem when you are approved.</p>
      <form id="invite-request" method="post" action="/invite/request" novalidate>
        <div class="field">
          <label for="email">Email</label>
          <input class="field__input" id="email" name="email" type="email" autocomplete="email" placeholder="you@studio.com" aria-describedby="email-error">
        </div>
        <p class="helper" id="email-error">Enter a valid email to request an invite.</p>
        <button class="btn btn--primary" type="submit">Request access</button>
        <a class="link" href="/invite/redeem">Already have a token? Redeem it.</a>
        <p class="foot" id="request-foot">No key yet — approval issues a one-time invite link.</p>
      </form>
    </div>
""",
    r"""
    const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
    const DEFAULT_SUB = "Join the waitlist. We email a one-time redeem when you are approved.";
    const ERROR_SUB = "We couldn’t add you to the waitlist. Check the email and try again.";

    const form = document.getElementById("invite-request");
    const card = document.getElementById("request-card");
    const emailInput = document.getElementById("email");
    const helper = document.getElementById("email-error");
    const sub = document.getElementById("request-sub");
    const foot = document.getElementById("request-foot");

    function isValidEmail(value) {
      const email = value.trim().toLowerCase();
      return EMAIL_RE.test(email) && email.length <= 254;
    }

    function showError() {
      card.classList.add("card--error");
      emailInput.setAttribute("aria-invalid", "true");
      helper.classList.add("is-visible");
      sub.textContent = ERROR_SUB;
      foot.hidden = true;
    }

    function clearError() {
      card.classList.remove("card--error");
      emailInput.removeAttribute("aria-invalid");
      helper.classList.remove("is-visible");
      sub.textContent = DEFAULT_SUB;
      foot.hidden = false;
    }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = emailInput.value;
      if (!isValidEmail(email)) {
        showError();
        return;
      }
      clearError();
      const res = await fetch("/invite/request", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email })
      });
      const data = await res.json();
      if (!res.ok) {
        showError();
        return;
      }
      window.location.href = "/invite/requested";
    });
""",
)

REQUESTED_HTML = _page(
    """
    <div class="card" id="requested-card">
      <p class="meta"><span class="pip" aria-hidden="true"></span>Invite · waitlist</p>
      <h1 class="title">You’re on the list</h1>
      <p class="sub">Thanks — we’ll email a one-time invite when your request is approved.</p>
      <p class="foot">Already have an invite? Open the link from your email to redeem.</p>
      <p class="foot foot--meta">No key on this screen — key appears only after a real redeem.</p>
    </div>
""",
    "",
)

REDEEM_HTML = _page(
    """
    <div class="card" id="redeem-card">
      <p class="meta"><span class="pip" aria-hidden="true"></span>Invite · redeem once</p>
      <p class="kicker" id="redeem-error-kicker"><span class="pip" aria-hidden="true"></span>REDEEM ERROR</p>
      <h1 class="title">Redeem invite</h1>
      <p class="sub" id="redeem-sub">Paste your invite token, or open the link from your email.</p>
      <form id="invite-redeem" method="post" action="/invite/redeem" novalidate>
        <div class="field">
          <label for="token">Invite token</label>
          <input class="field__input" id="token" name="token" type="text" autocomplete="off" spellcheck="false" placeholder="inv_••••••••••••" aria-describedby="token-error">
        </div>
        <p class="helper" id="token-error">Invite invalid or already used. Request a new one if needed.</p>
        <button class="btn btn--primary" type="submit">Redeem</button>
        <p class="foot" id="redeem-foot">Redeeming burns the invite and mints your uxmcp_ key once.</p>
        <p class="foot foot--exclusive">Error is exclusive — Success / key is not shown on this state.</p>
      </form>
    </div>
    <div class="card" id="success-card" hidden>
      <p class="meta"><span class="pip" aria-hidden="true"></span>Redeemed · key once</p>
      <h1 class="title">Your key</h1>
      <p class="sub">Invite redeemed. Copy your key — we won’t show it in full again.</p>
      <div class="key" id="key-text"></div>
      <button class="btn btn--primary" type="button" id="copy-key">Copy</button>
      <p class="foot">Use as bearer on /mcp. Self-host stdio needs no auth.</p>
    </div>
""",
    r"""
    const MASK = "uxmcp_" + "\u2022".repeat(16);
    const DEFAULT_SUB = "Paste your invite token, or open the link from your email.";
    const ERROR_SUB = "This invite isn’t valid. It may be used, expired, or mistyped.";
    let issuedKey = "";

    const form = document.getElementById("invite-redeem");
    const tokenInput = document.getElementById("token");
    const helper = document.getElementById("token-error");
    const sub = document.getElementById("redeem-sub");
    const foot = document.getElementById("redeem-foot");
    const redeemCard = document.getElementById("redeem-card");
    const successCard = document.getElementById("success-card");
    const keyText = document.getElementById("key-text");

    const params = new URLSearchParams(location.search);
    const q = params.get("token");
    if (q) tokenInput.value = q;

    function hideSuccess() {
      issuedKey = "";
      keyText.textContent = "";
      successCard.hidden = true;
    }

    function showError() {
      hideSuccess();
      redeemCard.hidden = false;
      redeemCard.classList.add("card--error");
      tokenInput.setAttribute("aria-invalid", "true");
      helper.classList.add("is-visible");
      sub.textContent = ERROR_SUB;
      foot.hidden = true;
    }

    function clearError() {
      redeemCard.classList.remove("card--error");
      tokenInput.removeAttribute("aria-invalid");
      helper.classList.remove("is-visible");
      sub.textContent = DEFAULT_SUB;
      foot.hidden = false;
    }

    function maskKey(key) {
      if (key.startsWith("uxmcp_")) return MASK;
      return "\u2022".repeat(16);
    }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const token = tokenInput.value.trim();
      if (!token) {
        showError();
        return;
      }
      clearError();
      const res = await fetch("/invite/redeem", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ token })
      });
      const data = await res.json();
      if (!res.ok || !data.key) {
        showError();
        return;
      }
      issuedKey = data.key;
      keyText.textContent = maskKey(issuedKey);
      redeemCard.hidden = true;
      successCard.hidden = false;
    });

    document.getElementById("copy-key").addEventListener("click", () => {
      if (!issuedKey || !navigator.clipboard) return;
      navigator.clipboard.writeText(issuedKey);
    });
""",
)
