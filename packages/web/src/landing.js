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
  <section class="flex w-full flex-wrap items-center justify-between gap-8 px-5 py-10 pb-8 md:px-12">
    <div class="flex w-[620px] max-w-full flex-col items-start gap-5">
      <p class="kicker"><span class="pip" aria-hidden="true"></span>Cited catalog · agents audit · no vibes</p>
      <h1 class="m-0 text-[40px] font-semibold leading-[44px] text-ink md:text-[52px] md:leading-[56px]">Open UX</h1>
      <p class="m-0 text-[22px] font-normal leading-7 text-ink">Cited UX rules agents audit against</p>
      <p class="m-0 text-[15px] leading-[22px] text-muted">Stop inventing UX rules from memory. Open UX is a shared, cited catalog agents list, fetch, and audit against.</p>
      <div class="flex flex-wrap items-center gap-5">
        <a class="btn btn-primary h-[38px]" href="/catalog">Browse catalog</a>
        <a class="btn btn-secondary h-[38px]" href="/invite">Request access</a>
      </div>
    </div>
    <aside class="flex w-[500px] max-w-full flex-col gap-3 rounded-sm border border-line bg-card p-4" aria-hidden="true">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2 font-mono text-[11px] text-muted">
          <span class="flex items-center">
            <span class="-mr-2.5 h-4 w-[22px] rounded bg-clay-back"></span>
            <span class="h-[22px] w-7 rounded bg-clay"></span>
          </span>
          topic · forms
        </div>
        <span class="font-mono text-[11px] font-medium text-pip">forms.field-labels</span>
      </div>
      <div class="flex w-full flex-col gap-1.5 rounded-sm border border-line bg-[#fffcf7] px-3 py-2.5">
        <p class="m-0 font-mono text-[10px] text-muted">jobs</p>
        <div class="flex items-center gap-2 text-[11px] text-ink"><span class="h-2 w-[72px] shrink-0 rounded bg-clay"></span>Visible labels on every field</div>
        <div class="flex items-center gap-2 text-[11px] text-ink"><span class="h-2 w-[72px] shrink-0 rounded bg-clay"></span>Placeholder is not the label</div>
        <div class="flex items-center gap-2 text-[11px] text-ink"><span class="h-2 w-[72px] shrink-0 rounded bg-clay"></span>Cite the rule, do not invent</div>
      </div>
      <div class="flex w-full items-center gap-2.5 rounded-sm bg-pip-soft px-3 py-2.5">
        <span class="size-[18px] shrink-0 rounded bg-pip"></span>
        <div>
          <p class="m-0 font-mono text-[10px] text-pip">citation</p>
          <p class="m-0 text-xs leading-4 text-ink">GOV.UK · labels sentence case, no colons, above</p>
        </div>
      </div>
      <div class="flex w-full gap-2">
        <div class="flex flex-1 flex-col gap-1 rounded-sm border border-success bg-success-bg px-2.5 py-2">
          <div class="flex items-center gap-1.5 font-mono text-[11px] font-medium text-success"><span class="pip pip-pass"></span>pass</div>
          <p class="m-0 text-[11px] leading-[14px] text-ink">cited rule · source attached</p>
        </div>
        <div class="flex flex-1 flex-col gap-1 rounded-sm border border-danger bg-danger-bg px-2.5 py-2">
          <div class="flex items-center gap-1.5 font-mono text-[11px] font-medium text-danger"><span class="pip pip-fail"></span>fail</div>
          <p class="m-0 text-[11px] leading-[14px] text-ink">invented rule · no source</p>
        </div>
      </div>
    </aside>
  </section>
  <section class="flex w-full flex-col items-start gap-4 px-5 py-4 pb-8 md:px-12">
    <h2 class="m-0 text-xl font-semibold leading-6 text-ink">How it works</h2>
    <div class="flex w-full flex-col items-stretch gap-4 md:flex-row">
      <article class="flex h-auto flex-1 flex-col gap-2.5 overflow-hidden rounded-sm border border-line bg-card p-4 md:h-[143px]">
        <div class="flex h-2.5 gap-1" aria-hidden="true"><span class="block h-2.5 w-7 rounded bg-clay"></span><span class="block h-2.5 w-[18px] rounded bg-clay-back"></span></div>
        <p class="m-0 font-mono text-[11px] font-medium text-pip">01</p>
        <h3 class="m-0 text-base font-semibold text-ink">Connect</h3>
        <p class="m-0 text-[13px] leading-[18px] text-muted">Install the Claude client (or any MCP client) and paste your key.</p>
      </article>
      <article class="flex h-auto flex-1 flex-col gap-2.5 overflow-hidden rounded-sm border border-line bg-card p-4 md:h-[143px]">
        <div class="flex h-2.5 gap-1" aria-hidden="true"><span class="block h-2.5 w-[22px] rounded bg-clay"></span><span class="block h-2.5 w-[26px] rounded bg-clay-back"></span></div>
        <p class="m-0 font-mono text-[11px] font-medium text-pip">02</p>
        <h3 class="m-0 text-base font-semibold text-ink">List · get</h3>
        <p class="m-0 text-[13px] leading-[18px] text-muted">Browse the shared catalog; every rule carries a citation.</p>
      </article>
      <article class="flex h-auto flex-1 flex-col gap-2.5 overflow-hidden rounded-sm border border-line bg-card p-4 md:h-[143px]">
        <div class="flex h-2.5 gap-1" aria-hidden="true"><span class="block h-2.5 w-4 rounded bg-clay-back"></span><span class="block h-2.5 w-[30px] rounded bg-clay"></span></div>
        <p class="m-0 font-mono text-[11px] font-medium text-pip">03</p>
        <h3 class="m-0 text-base font-semibold text-ink">Audit</h3>
        <p class="m-0 text-[13px] leading-[18px] text-muted">Say the compose job; get cited criteria. The host does not take a file or return pass or fail.</p>
      </article>
    </div>
  </section>
  </main>
  <section class="flex w-full flex-wrap items-center justify-between gap-4 border-y border-line bg-card px-5 py-5 md:px-12">
    <div>
      <h2 class="mb-1 mt-0 text-lg font-semibold text-ink">Join the community</h2>
      <p class="m-0 text-sm font-normal text-muted">Open UX is a shared idea — cited rules anyone can fork, cite, and improve together.</p>
    </div>
    <a class="text-sm font-medium text-pip no-underline" href="https://github.com/3dyonic/open-ux">View repo →</a>
  </section>`,
    {},
  );
}
