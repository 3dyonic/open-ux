"""Hosted invite HTML modules: Figma Request / Requested / Redeem / Success / Error.

Frames: Request 11:35, Requested 16:46, Redeem 16:70, Success 11:56, Error 11:78.
Admin 17:63 is CLI-only — not in this page.
"""

from __future__ import annotations

_CSS = """
    :root {
      --bg: #f6f8fa;
      --paper: #ffffff;
      --ink: #1f2328;
      --muted: #656d76;
      --line: #d0d7de;
      --accent: #0969da;
      --accent-bg: #ddf4ff;
      --danger: #cf222e;
      --success: #1a7f37;
      --radius: 6px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: ui-sans-serif, system-ui, sans-serif;
      line-height: 1.5;
      color: var(--ink);
      background: var(--bg);
    }
    .nav {
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      padding: 20px 48px;
      background: var(--paper);
      border-bottom: 1px solid var(--line);
    }
    .nav-brand {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .logo-mark {
      position: relative;
      width: 32px;
      height: 32px;
      background: var(--accent);
      border-radius: var(--radius);
      overflow: hidden;
      flex-shrink: 0;
    }
    .logo-bar {
      position: absolute;
      left: 7px;
      height: 2px;
      background: #fff;
      border-radius: 1px;
    }
    .logo-bar-1 { top: 9px; width: 18px; }
    .logo-bar-2 { top: 15px; width: 14px; }
    .logo-bar-3 { top: 21px; width: 10px; }
    .logo-dot {
      position: absolute;
      left: 20px;
      top: 20px;
      width: 6px;
      height: 6px;
      background: var(--accent-bg);
      border-radius: 1px;
    }
    .wordmark {
      font-size: 16px;
      font-weight: 600;
      color: var(--ink);
    }
    .nav-github {
      font-size: 14px;
      font-weight: 400;
      color: var(--muted);
      text-decoration: none;
    }
    .main {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 64px 48px 80px;
    }
    .card {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 16px;
      width: 440px;
      padding: 32px;
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: var(--radius);
    }
    .card[hidden] {
      display: none;
    }
    .kicker {
      display: none;
      margin: 0;
      font-size: 12px;
      font-weight: 600;
      color: var(--danger);
    }
    .card--error .kicker {
      display: block;
    }
    .card--error label {
      color: var(--muted);
    }
    .title {
      margin: 0;
      font-size: 24px;
      font-weight: 600;
      color: var(--ink);
    }
    .sub {
      margin: 0;
      font-size: 14px;
      font-weight: 400;
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
      font-size: 14px;
      font-weight: 600;
      color: var(--ink);
    }
    .field__input {
      width: 100%;
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--paper);
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
      color: var(--danger);
    }
    .helper.is-visible {
      display: block;
    }
    .foot {
      margin: 0;
      font-size: 12px;
      font-weight: 400;
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
      font-weight: 600;
      line-height: normal;
      cursor: pointer;
      text-decoration: none;
    }
    .btn--primary {
      background: var(--accent);
      color: var(--paper);
      border: none;
    }
    .key {
      width: 100%;
      padding: 12px;
      background: var(--accent-bg);
      border: 1px solid var(--accent);
      border-radius: var(--radius);
      font-size: 14px;
      font-weight: 600;
      color: var(--accent);
    }
"""

_NAV = """
  <header class="nav">
    <div class="nav-brand">
      <span class="logo-mark" aria-hidden="true">
        <span class="logo-bar logo-bar-1"></span>
        <span class="logo-bar logo-bar-2"></span>
        <span class="logo-bar logo-bar-3"></span>
        <span class="logo-dot"></span>
      </span>
      <span class="wordmark">Open UX</span>
    </div>
    <a class="nav-github" href="https://github.com/3dyonic/open-ux">GitHub</a>
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
      <p class="kicker" id="request-error-kicker">REQUEST ERROR</p>
      <h1 class="title">Request invite</h1>
      <p class="sub" id="request-sub">Join the waitlist. We’ll email a one-time invite when approved.</p>
      <form id="invite-request" method="post" action="/invite/request" novalidate>
        <div class="field">
          <label for="email">Email</label>
          <input class="field__input" id="email" name="email" type="email" autocomplete="email" placeholder="you@company.com" aria-describedby="email-error">
        </div>
        <p class="helper" id="email-error">Enter a valid email to request an invite.</p>
        <button class="btn btn--primary" type="submit">Request invite</button>
        <p class="foot" id="request-foot">No key yet — approval issues a one-time invite link.</p>
      </form>
    </div>
""",
    r"""
    const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
    const DEFAULT_SUB = "Join the waitlist. We’ll email a one-time invite when approved.";
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
      <h1 class="title">You’re on the list</h1>
      <p class="sub">Thanks — we’ll email a one-time invite when your request is approved.</p>
      <p class="foot">Already have an invite? Open the link from your email to redeem.</p>
    </div>
""",
    "",
)

REDEEM_HTML = _page(
    """
    <div class="card" id="redeem-card">
      <p class="kicker" id="redeem-error-kicker">REDEEM ERROR</p>
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
      </form>
    </div>
    <div class="card" id="success-card" hidden>
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
