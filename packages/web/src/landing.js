import { shell } from "./chrome.js";
import { setTitle } from "./util.js";

export function renderLanding(root) {
  setTitle("Open UX — Cited UX rules agents audit against");
  if (location.hash === "#register") {
    location.replace("/invite");
    return;
  }
  root.innerHTML = shell(
    `
  <main>
  <section class="hero">
    <div class="hero-copy">
      <p class="kicker"><span class="pip" aria-hidden="true"></span>Cited catalog · agents audit · no vibes</p>
      <h1>Open UX</h1>
      <p class="sub">Cited UX rules agents audit against</p>
      <p class="hero-body">Stop inventing UX rules from memory. Open UX is a shared, cited catalog agents list, fetch, and audit against.</p>
      <div class="ctas">
        <a class="btn btn--primary" href="/catalog">Browse catalog</a>
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
        <span class="ill-id">forms.field-labels</span>
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
          <p class="cite-copy">GOV.UK · labels sentence case, no colons, above</p>
        </div>
      </div>
      <div class="chips chips--hero">
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
        <p>Say the compose job; get cited criteria. The host does not take a file or return pass or fail.</p>
      </article>
    </div>
  </section>
  </main>
  <section class="cta-band">
    <div class="cta-copy">
      <h2>Join the community</h2>
      <p>Open UX is a shared idea — cited rules anyone can fork, cite, and improve together.</p>
    </div>
    <a class="oss-link" href="https://github.com/3dyonic/open-ux">View repo →</a>
  </section>`,
    {},
  );
}
