import { shell } from "./chrome.js";
import { escapeHtml, setTitle } from "./util.js";

function chip(label, degraded = false) {
  const cls = degraded ? "chip chip--status chip--degraded" : "chip chip--status";
  return `<span class="${cls}"><span class="pip" aria-hidden="true"></span>${escapeHtml(label)}</span>`;
}

function render(root, payload) {
  const catalog = payload.catalog || {};
  const systemsOk = Boolean(payload.ok) && catalog.status === "ok";
  const hosted = Boolean(payload.hosted);
  const statusTitle = systemsOk
    ? "Success: host and catalog are up"
    : "Error: catalog is not loaded";
  const statusBody = systemsOk
    ? "The hosted service is running. The catalog is loaded."
    : "The host is up. The catalog has no cited rules yet. Browse the catalog when rules land.";
  const bannerCls = systemsOk ? "status-banner" : "status-banner is-degraded";
  const hostedLine = hosted
    ? "Running on the hosted service."
    : "Running locally, not on the hosted service.";
  const catalogLine = systemsOk
    ? `${catalog.guideline_count} cited rules, version ${catalog.version}`
    : "No cited rules loaded yet.";
  root.innerHTML = shell(
    `
  <main class="main">
    <p class="kicker"><span class="pip" aria-hidden="true"></span>Status</p>
    <div class="${bannerCls}" role="region" aria-label="Status">
      <span class="status-pip" aria-hidden="true"></span>
      <div class="status-copy">
        <p class="status-title">${escapeHtml(statusTitle)}</p>
        <p class="status-map">${escapeHtml(statusBody)}</p>
      </div>
      <span class="banner-spacer"></span>
      ${chip(systemsOk ? "Operational" : "Not loaded", !systemsOk)}
    </div>
    <div class="header">
      <div class="header-copy">
        <h1>Health</h1>
        <p class="lede">Whether the hosted service is up, and whether the catalog is loaded.</p>
        <a class="browse" href="/catalog">Browse catalog →</a>
      </div>
    </div>
    <section class="components">
      <h2 class="components-title">Components</h2>
      <div class="component-list">
        <div class="component-row">
          <div class="row-left">
            <p class="component-name">API</p>
            <p class="component-hint">The service answers requests.</p>
          </div>
          ${chip("Operational")}
        </div>
        <div class="component-row">
          <div class="row-left">
            <p class="component-name">Hosted service</p>
            <p class="component-meta">${escapeHtml(hostedLine)}</p>
          </div>
          ${chip(hosted ? "Operational" : "Local", !hosted)}
        </div>
        <div class="component-row">
          <div class="row-left">
            <p class="component-name">Catalog</p>
            <p class="component-meta">${escapeHtml(String(catalogLine))}</p>
          </div>
          ${chip(systemsOk ? "Operational" : "Not loaded", !systemsOk)}
        </div>
      </div>
    </section>
    <section class="about">
      <h2 class="about-title">About</h2>
      <p class="about-body">This page shows whether Open UX is up. Agents that ask for JSON get the same facts.</p>
    </section>
    <p class="browse-row">
      <span class="browse-note">Need the rules?</span>
      <a class="browse" href="/catalog">Browse catalog →</a>
    </p>
  </main>`,
    { paper: true, key: false },
  );
}

export async function renderHealth(root) {
  setTitle("Health — Open UX");
  root.innerHTML = shell(`<main class="main"><p class="lede">Loading status…</p></main>`, {
    paper: true,
    key: false,
  });
  try {
    const res = await fetch("/health.json");
    const data = await res.json();
    render(root, data);
  } catch {
    render(root, {
      ok: false,
      hosted: false,
      catalog: { status: "empty", guideline_count: 0, version: "" },
    });
  }
}
