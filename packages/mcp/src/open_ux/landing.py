"""Public `/` HTML: Figma marketing chrome plus the existing register form."""

from __future__ import annotations

LANDING_HTML = """<!DOCTYPE html>
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
      --danger: #cf222e;
      --danger-bg: #ffebe9;
      --success: #1a7f37;
      --success-bg: #dafbe1;
      --radius: 6px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: ui-sans-serif, system-ui, sans-serif;
      line-height: 1.5;
      color: var(--ink);
      background: var(--bg);
    }
    a { color: inherit; }
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
    .hero {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;
      width: 100%;
      padding: 80px 48px 64px;
      background: var(--paper);
      text-align: center;
    }
    .hero-micro {
      margin: 0;
      font-size: 13px;
      font-weight: 500;
      color: var(--accent);
    }
    h1 {
      margin: 0;
      font-size: 48px;
      font-weight: 600;
      line-height: normal;
      color: var(--ink);
    }
    .sub {
      margin: 0;
      font-size: 20px;
      font-weight: 400;
      color: var(--muted);
    }
    .hero-body {
      margin: 0;
      max-width: 640px;
      font-size: 16px;
      color: var(--ink);
    }
    .ctas {
      display: flex;
      gap: 12px;
      align-items: flex-start;
    }
    .cta {
      display: inline-block;
      padding: 10px 16px;
      border-radius: var(--radius);
      font-size: 14px;
      font-weight: 600;
      line-height: normal;
      text-decoration: none;
    }
    .cta-primary {
      background: var(--accent);
      color: var(--paper);
    }
    .cta-secondary {
      background: var(--paper);
      color: var(--ink);
      border: 1px solid var(--line);
    }
    .register {
      max-width: 42rem;
      margin: 0 auto;
      padding: 0 1rem 64px;
      background: var(--paper);
    }
    .register-wrap {
      width: 100%;
      background: var(--paper);
    }
    label { display: block; margin: 0.75rem 0 0.25rem; }
    input { width: 100%; padding: 0.4rem; }
    button { margin-top: 0.75rem; padding: 0.4rem 0.8rem; }
    .out { white-space: pre-wrap; background: #1111; padding: 0.75rem; min-height: 2rem; }
    .warn { font-size: 0.9rem; }
    code, pre { font-family: ui-monospace, monospace; font-size: 0.9em; }
    .how {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 24px;
      width: 100%;
      padding: 48px 48px 64px;
      background: var(--paper);
    }
    .how h2 {
      margin: 0;
      font-size: 24px;
      font-weight: 600;
      color: var(--ink);
    }
    .how-cards {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 16px;
    }
    .how-card {
      width: 360px;
      padding: 20px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--bg);
    }
    .how-card h3 {
      margin: 0 0 8px;
      font-size: 16px;
      font-weight: 600;
      color: var(--ink);
    }
    .how-card p {
      margin: 0;
      font-size: 14px;
      color: var(--muted);
    }
    .verdicts {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
      width: 100%;
      padding: 32px 48px;
      background: var(--bg);
    }
    .verdict {
      display: inline-block;
      padding: 12px 16px;
      border-radius: var(--radius);
      font-size: 14px;
      font-weight: 600;
      line-height: normal;
    }
    .verdict-fail {
      color: var(--danger);
      background: var(--danger-bg);
      border: 1px solid var(--danger);
    }
    .verdict-pass {
      color: var(--success);
      background: var(--success-bg);
      border: 1px solid var(--success);
    }
    .footer {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      width: 100%;
      padding: 40px 48px 48px;
      background: var(--paper);
      border-top: 1px solid var(--line);
      font-size: 13px;
      color: var(--muted);
      text-align: center;
    }
    .footer p { margin: 0; }
  </style>
</head>
<body>
  <header class="nav">
    <span class="nav-brand">Open UX</span>
    <a class="nav-github" href="https://github.com/3dyonic/open-ux">GitHub</a>
  </header>
  <section class="hero">
    <p class="hero-micro">v1 — Forms → field labels · one catalog · no vibes</p>
    <h1>Open UX</h1>
    <p class="sub">Cited UX rules agents audit against</p>
    <p class="hero-body">Stop inventing UX rules from memory. Open UX is a shared, cited catalog agents list, fetch, and audit against.</p>
    <div class="ctas">
      <a class="cta cta-primary" id="get-key" href="#register">Get a key</a>
      <a class="cta cta-secondary" href="https://github.com/3dyonic/open-ux">View on GitHub</a>
    </div>
  </section>
  <div class="register-wrap">
  <section class="register" id="register">
  <p>Install path: <strong>connect → key → list → one audit</strong>.</p>
  <p>Hosted calls need a bearer key. Register with email (issue / revoke only). Self-host stdio needs no key.</p>
  <form id="reg">
    <label for="email">Email</label>
    <input id="email" name="email" type="email" required autocomplete="email">
    <button type="submit">Register</button>
  </form>
  <p class="warn">The key is shown once. Put URL + key in client settings (Thursday path). Catalog is empty until cited seed rules land.</p>
  <pre class="out" id="out"></pre>
  </section>
  </div>
  <section class="how">
    <h2>How it works</h2>
    <div class="how-cards">
      <article class="how-card">
        <h3>1. Connect</h3>
        <p>Install the Claude client (or any MCP client) and paste your key.</p>
      </article>
      <article class="how-card">
        <h3>2. List / get</h3>
        <p>Browse the shared catalog; every rule carries a citation.</p>
      </article>
      <article class="how-card">
        <h3>3. Audit</h3>
        <p>Send UI (html / jsx / description); get pass, fail, or incomplete with the rule id — not a guess.</p>
      </article>
    </div>
  </section>
  <section class="verdicts">
    <span class="verdict verdict-fail">fail · placeholder-only label</span>
    <span class="verdict verdict-pass">pass · visible label present</span>
  </section>
  <footer class="footer">
    <p>One open catalog. Registration gates who may call — not which rules exist.</p>
    <p>Privacy: no raw audit content in logs.</p>
  </footer>
  <script>
    document.getElementById('reg').addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('email').value;
      const res = await fetch('/register', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ email })
      });
      const data = await res.json();
      document.getElementById('out').textContent = JSON.stringify(data, null, 2);
    });
    document.getElementById('get-key').addEventListener('click', () => {
      document.getElementById('email').focus();
    });
  </script>
</body>
</html>
"""
