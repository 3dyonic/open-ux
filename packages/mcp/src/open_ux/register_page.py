"""Public GET `/register` HTML: Figma Get a key Form / Success / Error."""

from __future__ import annotations

REGISTER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Open UX</title>
  <style>
    :root {
      --bg: #f6f8fa;
      --paper: #ffffff;
      --ink: #1f2328;
      --muted: #656d76;
      --line: #d0d7de;
      --accent: #0969da;
      --accent-bg: #ddf4ff;
      --danger: #cf222e;
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
    input {
      width: 100%;
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--paper);
      color: var(--ink);
      font-family: inherit;
      font-size: 14px;
    }
    input::placeholder {
      color: var(--muted);
    }
    input.is-invalid {
      border-color: var(--danger);
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
    .btn-primary {
      background: var(--accent);
      color: var(--paper);
      border: none;
    }
    .btn-secondary {
      background: var(--paper);
      color: var(--ink);
      border: 1px solid var(--line);
    }
    .actions {
      display: flex;
      gap: 12px;
      align-items: flex-start;
    }
    .key-box {
      width: 100%;
      padding: 12px;
      background: var(--accent-bg);
      border: 1px solid var(--accent);
      border-radius: var(--radius);
    }
    .key-text {
      margin: 0;
      font-size: 14px;
      font-weight: 600;
      color: var(--accent);
    }
  </style>
</head>
<body>
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
  <main class="main" id="register">
    <div class="card" id="form-card">
      <p class="title">Get a key</p>
      <p class="sub">Email in → API key out. One shared catalog; registration only gates who may call.</p>
      <form id="reg" novalidate>
        <div class="field">
          <label for="email">Email</label>
          <input id="email" name="email" type="email" autocomplete="email" placeholder="you@company.com" aria-describedby="email-error">
        </div>
        <p class="helper" id="email-error">Enter a valid email so we can mint your key.</p>
        <button class="btn btn-primary" type="submit">Get a key</button>
        <p class="foot" id="form-foot">No marketing mail — this only mints your uxmcp_ key.</p>
      </form>
    </div>
    <div class="card" id="success-card" hidden>
      <p class="title">Your key</p>
      <p class="sub">Save this key — we won’t show it again in full.</p>
      <div class="key-box">
        <p class="key-text" id="key-text">uxmcp_••••••••••••••••</p>
      </div>
      <div class="actions">
        <button class="btn btn-primary" type="button" id="copy-key">Copy key</button>
        <a class="btn btn-secondary" id="back-home" href="/">Back to home</a>
      </div>
      <p class="foot">Point your client at /mcp with this bearer key.</p>
    </div>
  </main>
  <script>
    const EMAIL_RE = /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/;
    const MASK = 'uxmcp_' + '\\u2022'.repeat(16);
    let issuedKey = '';

    const form = document.getElementById('reg');
    const emailInput = document.getElementById('email');
    const helper = document.getElementById('email-error');
    const formFoot = document.getElementById('form-foot');
    const formCard = document.getElementById('form-card');
    const successCard = document.getElementById('success-card');
    const keyText = document.getElementById('key-text');

    function isValidEmail(value) {
      const email = value.trim().toLowerCase();
      return EMAIL_RE.test(email) && email.length <= 254;
    }

    function maskKey(key) {
      if (key.startsWith('uxmcp_')) return MASK;
      return '\\u2022'.repeat(16);
    }

    function showError() {
      emailInput.classList.add('is-invalid');
      emailInput.setAttribute('aria-invalid', 'true');
      helper.classList.add('is-visible');
      formFoot.hidden = true;
    }

    function clearError() {
      emailInput.classList.remove('is-invalid');
      emailInput.removeAttribute('aria-invalid');
      helper.classList.remove('is-visible');
      formFoot.hidden = false;
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = emailInput.value;
      if (!isValidEmail(email)) {
        showError();
        return;
      }
      clearError();
      const res = await fetch('/register', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ email })
      });
      const data = await res.json();
      if (!res.ok || !data.key) {
        showError();
        return;
      }
      issuedKey = data.key;
      keyText.textContent = maskKey(issuedKey);
      formCard.hidden = true;
      successCard.hidden = false;
    });

    document.getElementById('copy-key').addEventListener('click', () => {
      if (!issuedKey || !navigator.clipboard) return;
      navigator.clipboard.writeText(issuedKey);
    });
  </script>
</body>
</html>
"""
