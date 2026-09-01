"""Public `/` HTML: F3 paper/ink/pip chrome. Get a key CTA goes to `/invite`."""

from __future__ import annotations

LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Open UX</title>
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
      --pip-soft: #FFECE0;
      --clay: #ecdcca;
      --clay-back: #d6bea6;
      --danger: #B82A2A;
      --danger-bg: #fdecec;
      --success: #1A7F37;
      --success-bg: #e7f6ec;
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
    .pip {
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--pip);
      flex-shrink: 0;
    }
    .pip--pass { background: var(--success); }
    .pip--fail { background: var(--danger); }
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
    .btn--secondary {
      background: transparent;
      color: var(--ink);
      border: 1px solid var(--ink);
      padding: 9px 15px;
    }
    .hero {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 32px;
      width: 100%;
      padding: 40px 48px 32px;
    }
    .hero-copy {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 14px;
      width: 620px;
      max-width: 100%;
    }
    .kicker {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0;
      font-family: var(--mono);
      font-size: 11px;
      font-weight: 400;
      color: var(--muted);
    }
    h1 {
      margin: 0;
      font-size: 52px;
      font-weight: 600;
      line-height: 56px;
      color: var(--ink);
    }
    .sub {
      margin: 0;
      font-size: 22px;
      font-weight: 400;
      line-height: 28px;
      color: var(--ink);
    }
    .hero-body {
      margin: 0;
      font-size: 15px;
      line-height: 22px;
      color: var(--muted);
    }
    .ctas {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
    }
    .ill {
      display: flex;
      flex-direction: column;
      gap: 12px;
      width: 500px;
      max-width: 100%;
      padding: 16px;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: var(--radius);
    }
    .ill-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .ill-topic {
      display: flex;
      align-items: center;
      gap: 8px;
      font-family: var(--mono);
      font-size: 11px;
      color: var(--muted);
    }
    .topic-stack {
      display: flex;
      align-items: center;
    }
    .clay-topic-back {
      width: 22px;
      height: 16px;
      margin-right: -10px;
      background: var(--clay-back);
      border-radius: 4px;
    }
    .clay-topic {
      width: 28px;
      height: 22px;
      background: var(--clay);
      border-radius: 4px;
    }
    .ill-id {
      font-family: var(--mono);
      font-size: 11px;
      font-weight: 500;
      color: var(--pip);
    }
    .ill-jobs {
      display: flex;
      flex-direction: column;
      gap: 6px;
      width: 100%;
      padding: 10px 12px;
      background: #fffcf7;
      border: 1px solid var(--line);
      border-radius: var(--radius);
    }
    .ill-jobs-label {
      margin: 0;
      font-family: var(--mono);
      font-size: 10px;
      color: var(--muted);
    }
    .job {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 11px;
      color: var(--ink);
    }
    .clay-bar {
      width: 72px;
      height: 8px;
      background: var(--clay);
      border-radius: 4px;
      flex-shrink: 0;
    }
    .ill-citation {
      display: flex;
      align-items: center;
      gap: 10px;
      width: 100%;
      padding: 10px 12px;
      background: var(--pip-soft);
      border-radius: var(--radius);
    }
    .clay-quote {
      width: 18px;
      height: 18px;
      background: var(--pip);
      border-radius: 4px;
      flex-shrink: 0;
    }
    .cite-kicker {
      margin: 0;
      font-family: var(--mono);
      font-size: 10px;
      color: var(--pip);
    }
    .cite-copy {
      margin: 0;
      font-size: 12px;
      line-height: 16px;
      color: var(--ink);
    }
    .chips {
      display: flex;
      gap: 8px;
      width: 100%;
    }
    .chip {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding: 8px 10px;
      border-radius: var(--radius);
    }
    .chip-top {
      display: flex;
      align-items: center;
      gap: 6px;
      font-family: var(--mono);
      font-size: 11px;
      font-weight: 500;
    }
    .chip p {
      margin: 0;
      font-size: 11px;
      line-height: 14px;
      color: var(--ink);
    }
    .chip--pass {
      background: var(--success-bg);
      border: 1px solid var(--success);
    }
    .chip--pass .chip-top { color: var(--success); }
    .chip--fail {
      background: var(--danger-bg);
      border: 1px solid var(--danger);
    }
    .chip--fail .chip-top { color: var(--danger); }
    .how {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 16px;
      width: 100%;
      padding: 16px 48px 32px;
    }
    .how h2 {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
      line-height: 24px;
      color: var(--ink);
    }
    .how-cards {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      width: 100%;
    }
    .how-card {
      flex: 1 1 280px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--card);
    }
    .clay-step {
      display: flex;
      gap: 4px;
      height: 10px;
    }
    .clay-step span {
      display: block;
      height: 10px;
      border-radius: 4px;
      background: var(--clay);
    }
    .clay-step-1 span:nth-child(1) { width: 28px; }
    .clay-step-1 span:nth-child(2) { width: 18px; background: var(--clay-back); }
    .clay-step-2 span:nth-child(1) { width: 22px; }
    .clay-step-2 span:nth-child(2) { width: 26px; background: var(--clay-back); }
    .clay-step-3 span:nth-child(1) { width: 16px; background: var(--clay-back); }
    .clay-step-3 span:nth-child(2) { width: 30px; }
    .how-num {
      margin: 0;
      font-family: var(--mono);
      font-size: 11px;
      font-weight: 500;
      color: var(--pip);
    }
    .how-card h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--ink);
    }
    .how-card p {
      margin: 0;
      font-size: 13px;
      line-height: 18px;
      color: var(--muted);
    }
    .cta-band {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      width: 100%;
      padding: 20px 48px;
      background: var(--card);
      border-top: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
    }
    .cta-copy h2 {
      margin: 0 0 4px;
      font-size: 18px;
      font-weight: 600;
      color: var(--ink);
    }
    .cta-copy p {
      margin: 0;
      font-size: 13px;
      color: var(--muted);
    }
    .footer {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      width: 100%;
      padding: 16px 48px 24px;
      font-size: 12px;
      color: var(--muted);
    }
    .footer p { margin: 0; }
    .footer-repo {
      font-family: var(--mono);
      font-size: 11px;
    }
  </style>
</head>
<body>
  <header class="nav">
    <span class="nav-brand"><span class="pip" aria-hidden="true"></span>Open UX</span>
    <div class="nav-actions">
      <a class="nav-github" href="https://github.com/3dyonic/open-ux">GitHub</a>
      <a class="btn btn--primary btn--nav" href="/invite">Get a key</a>
    </div>
  </header>
  <section class="hero">
    <div class="hero-copy">
      <p class="kicker"><span class="pip" aria-hidden="true"></span>Cited catalog · agents audit · no vibes</p>
      <h1>Open UX</h1>
      <p class="sub">Cited UX rules agents audit against</p>
      <p class="hero-body">Stop inventing UX rules from memory. Open UX is a shared, cited catalog agents list, fetch, and audit against.</p>
      <div class="ctas">
        <a class="btn btn--primary" id="get-key" href="/invite">Get a key</a>
        <a class="btn btn--secondary" href="/invite">Request access</a>
      </div>
    </div>
    <aside class="ill" aria-hidden="true">
      <div class="ill-head">
        <div class="ill-topic">
          <span class="topic-stack">
            <span class="clay-topic-back"></span>
            <span class="clay-topic"></span>
          </span>
          topic · forms
        </div>
        <span class="ill-id">uns-44</span>
      </div>
      <div class="ill-jobs">
        <p class="ill-jobs-label">jobs</p>
        <div class="job"><span class="clay-bar"></span>Visible labels on every field</div>
        <div class="job"><span class="clay-bar"></span>Placeholder is not the label</div>
        <div class="job"><span class="clay-bar"></span>Cite the rule, do not invent</div>
      </div>
      <div class="ill-citation">
        <span class="clay-quote"></span>
        <div>
          <p class="cite-kicker">citation</p>
          <p class="cite-copy">NN/g · field labels stay visible while typing</p>
        </div>
      </div>
      <div class="chips">
        <div class="chip chip--pass">
          <div class="chip-top"><span class="pip pip--pass"></span>pass</div>
          <p>cited rule · source attached</p>
        </div>
        <div class="chip chip--fail">
          <div class="chip-top"><span class="pip pip--fail"></span>fail</div>
          <p>invented rule · no source</p>
        </div>
      </div>
    </aside>
  </section>
  <section class="how">
    <h2>How it works</h2>
    <div class="how-cards">
      <article class="how-card">
        <div class="clay-step clay-step-1" aria-hidden="true"><span></span><span></span></div>
        <p class="how-num">01</p>
        <h3>Connect</h3>
        <p>Install the Claude client (or any MCP client) and paste your key.</p>
      </article>
      <article class="how-card">
        <div class="clay-step clay-step-2" aria-hidden="true"><span></span><span></span></div>
        <p class="how-num">02</p>
        <h3>List · get</h3>
        <p>Browse the shared catalog; every rule carries a citation.</p>
      </article>
      <article class="how-card">
        <div class="clay-step clay-step-3" aria-hidden="true"><span></span><span></span></div>
        <p class="how-num">03</p>
        <h3>Audit</h3>
        <p>Send UI (html / jsx / description); get pass, fail, or incomplete with the rule id.</p>
      </article>
    </div>
  </section>
  <section class="cta-band">
    <div class="cta-copy">
      <h2>Request access</h2>
      <p>Join the waitlist. One key after approve and redeem — no vibes.</p>
    </div>
    <a class="btn btn--primary" href="/invite">Get a key</a>
  </section>
  <footer class="footer">
    <p>Open UX · cited UX rules agents audit against</p>
    <p class="footer-repo"><a href="https://github.com/3dyonic/open-ux">github.com/3dyonic/open-ux</a></p>
  </footer>
  <script>
    if (location.hash === '#register') location.replace('/invite');
  </script>
</body>
</html>
"""
