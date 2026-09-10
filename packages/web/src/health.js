import { shell } from "./chrome.js";
import { escapeHtml, setTitle, ssr } from "./util.js";

const CHROME = { paper: true, key: false, consent: false };

function chip(label, tone = "ok") {
  const cls =
    tone === "bad"
      ? "status-chip status-chip-bad"
      : tone === "neutral"
        ? "status-chip status-chip-neutral"
        : "status-chip";
  const dot =
    tone === "bad"
      ? "pip-tiny pip-tiny-danger"
      : tone === "neutral"
        ? "pip-tiny pip-tiny-muted"
        : "pip-tiny";
  return `<span class="${cls}"><span class="${dot}" aria-hidden="true"></span>${escapeHtml(label)}</span>`;
}

function render(root, payload) {
  const catalog = payload.catalog || {};
  const catalogOk = catalog.status === "ok";
  const error = payload.error && typeof payload.error === "object" ? payload.error : null;
  const systemsOk = Boolean(payload.ok) && !error && catalogOk;
  const hosted = Boolean(payload.hosted);
  const statusTitle = payload.title || (systemsOk
    ? "Success: host and catalog are up"
    : "Error: catalog is not loaded");
  const statusBody = payload.body || (systemsOk
    ? "The hosted service is running. The catalog is loaded."
    : "The host is up. The catalog has no cited rules yet. Browse the catalog when rules land.");
  const pipCls = systemsOk
    ? "size-2.5 shrink-0 rounded-full bg-success"
    : "size-2.5 shrink-0 rounded-full bg-danger";
  const hostedLine = hosted
    ? "Running on the hosted service."
    : "Running locally, not on the hosted service.";
  const catalogLine = catalogOk
    ? `${catalog.guideline_count} cited rules`
    : "No cited rules loaded yet.";
  const apiLine = error
    ? `A request returned ${error.status}.${error.path ? ` ${error.path}` : ""}`
    : "The service answers requests.";
  const bannerChip = error
    ? chip("Error", "bad")
    : chip(systemsOk ? "Operational" : "Not loaded", systemsOk ? "ok" : "bad");
  root.innerHTML = shell(
    `
  <main class="page">
    <p class="kicker"><span class="pip" aria-hidden="true"></span>Status</p>
    <div class="flex w-full items-center gap-3 rounded-sm border border-line bg-card px-4 py-3.5" role="region" aria-label="Status">
      <span class="${pipCls}" aria-hidden="true"></span>
      <div class="flex min-w-0 flex-col gap-0.5">
        <p class="m-0 text-base font-semibold text-ink">${escapeHtml(statusTitle)}</p>
        <p class="m-0 font-mono text-xs text-muted">${escapeHtml(statusBody)}</p>
      </div>
      <span class="flex-1"></span>
      ${bannerChip}
    </div>
    <div class="flex flex-col gap-3">
      <h1 class="page-title font-semibold">Health</h1>
      <p class="lede">Whether the hosted service is up, and whether the catalog is loaded.</p>
      <a class="text-sm font-medium text-pip hover:underline focus:underline" href="/catalog">Browse catalog →</a>
    </div>
    <section class="flex w-full flex-col gap-3">
      <h2 class="m-0 text-sm font-semibold text-ink">Components</h2>
      <div class="w-full overflow-hidden rounded-sm border border-line bg-card">
        <div class="flex w-full items-center justify-between gap-4 border-b border-line p-4">
          <div class="flex min-w-0 flex-col gap-1">
            <p class="m-0 text-base font-medium text-ink">API</p>
            <p class="m-0 font-mono text-[13px] text-muted">${escapeHtml(apiLine)}</p>
          </div>
          ${chip(error ? "Error" : "Operational", error ? "bad" : "ok")}
        </div>
        <div class="flex w-full items-center justify-between gap-4 border-b border-line p-4">
          <div class="flex min-w-0 flex-col gap-1">
            <p class="m-0 text-base font-medium text-ink">Hosted service</p>
            <p class="m-0 font-mono text-[13px] text-muted">${escapeHtml(hostedLine)}</p>
          </div>
          ${chip(hosted ? "Operational" : "Local", hosted ? "ok" : "neutral")}
        </div>
        <div class="flex w-full items-center justify-between gap-4 p-4">
          <div class="flex min-w-0 flex-col gap-1">
            <p class="m-0 text-base font-medium text-ink">Catalog</p>
            <p class="m-0 font-mono text-[13px] text-muted">${escapeHtml(String(catalogLine))}</p>
          </div>
          ${chip(catalogOk ? "Operational" : "Not loaded", catalogOk ? "ok" : "bad")}
        </div>
      </div>
    </section>
    <section class="flex w-full flex-col gap-2 rounded-sm border border-line bg-paper px-4 py-3.5">
      <h2 class="m-0 text-[13px] font-semibold text-ink">About</h2>
      <p class="m-0 text-sm text-muted">This page shows whether Open UX is up. Agents that ask for JSON get the same facts.</p>
    </section>
    <p class="flex flex-wrap items-center gap-2 text-sm">
      <span class="m-0 text-muted">Need the rules?</span>
      <a class="text-sm font-medium text-pip hover:underline focus:underline" href="/catalog">Browse catalog →</a>
    </p>
  </main>`,
    CHROME,
  );
}

export function healthPage() {
  return {
    title: "Health — Open UX",
    description: "Whether the hosted service is up, and whether the catalog is loaded.",
    path: "/health",
    index: false,
    body: ssr(
      "health",
      shell(
        `
  <main class="page">
    <p class="kicker"><span class="pip" aria-hidden="true"></span>Status</p>
    <h1 class="page-title font-semibold">Health</h1>
    <p class="lede">Whether the hosted service is up, and whether the catalog is loaded.</p>
  </main>`,
        CHROME,
      ),
    ),
  };
}

export async function renderHealth(root) {
  setTitle("Health — Open UX");
  if (!root.querySelector('[data-ssr-page="health"]')) {
    root.innerHTML = shell(
      `<main class="page"><p class="lede">Loading status…</p></main>`,
      CHROME,
    );
  }
  try {
    const res = await fetch("/health.json");
    const data = await res.json();
    render(root, data);
  } catch {
    render(root, {
      ok: false,
      hosted: false,
      title: "Error: status could not be loaded",
      body: "Try this page again.",
      error: { status: 500, path: "/health.json" },
      catalog: { status: "empty", guideline_count: 0 },
    });
  }
}
