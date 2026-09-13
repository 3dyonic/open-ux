import { shell } from "./chrome.js";
import { escapeHtml, setTitle, ssr } from "./util.js";

const TOKEN_KEY = "open_ux_admin_token";

const TELEMETRY_TITLE = "Telemetry — Open UX";
const TELEMETRY_DESCRIPTION = "Admin telemetry summary.";

function setBusy(button, busy, idleLabel, busyLabel) {
  button.disabled = busy;
  button.setAttribute("aria-busy", busy ? "true" : "false");
  button.classList.toggle("btn-busy", busy);
  button.textContent = busy ? busyLabel : idleLabel;
}

function readToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY) || "";
  } catch {
    return "";
  }
}

function writeToken(token) {
  try {
    sessionStorage.setItem(TOKEN_KEY, token);
  } catch {
    // sessionStorage unavailable — token just won't survive a reload.
  }
}

function clearToken() {
  try {
    sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    // nothing to clear
  }
}

async function adminFetch(token, path) {
  return fetch(path, { headers: { Authorization: `Bearer ${token}` } });
}

export function telemetryPage() {
  return {
    title: TELEMETRY_TITLE,
    description: TELEMETRY_DESCRIPTION,
    path: "/admin/telemetry",
    index: false,
    body: ssr(
      "admin-telemetry",
      shell(
        `
  <main class="page">
    <div class="flex w-full flex-1 flex-col items-center justify-center" id="admin-login-view">
      <div class="invite-card" id="admin-login-card">
        <p class="invite-meta"><span class="pip" aria-hidden="true"></span>Admin · telemetry</p>
        <h1 class="invite-title">Admin sign-in</h1>
        <p class="invite-sub" id="admin-login-sub">Paste the admin bearer token to view telemetry.</p>
        <form id="admin-login" class="contents" novalidate>
          <div class="field-invite">
            <label class="label-invite" for="admin-token">Admin token</label>
            <div class="flex w-full items-center gap-2">
              <input class="input input-invite flex-1" id="admin-token" name="token" type="password" autocomplete="off" spellcheck="false" autocapitalize="none" placeholder="paste token">
              <button class="btn btn-outline btn-nav" type="button" id="admin-token-toggle" aria-pressed="false">Show</button>
            </div>
          </div>
          <button class="btn btn-primary" type="submit" id="admin-login-submit">Sign in</button>
          <p class="foot" id="admin-login-foot">Kept only for this tab — never sent anywhere but this site's /admin endpoints.</p>
        </form>
      </div>
    </div>

    <div class="flex w-full flex-col gap-7" id="admin-stats-view" hidden>
      <div class="flex items-center justify-between gap-4">
        <div class="flex flex-col gap-1">
          <p class="invite-meta"><span class="pip" aria-hidden="true"></span>Admin · telemetry</p>
          <h1 class="page-title">Telemetry</h1>
        </div>
        <div class="flex items-center gap-4">
          <nav class="flex items-center gap-3 text-sm">
            <a class="text-muted" href="/admin">Invites</a>
            <span class="font-semibold text-ink">Telemetry</span>
          </nav>
          <button class="btn btn-outline btn-nav" type="button" id="admin-logout">Sign out</button>
        </div>
      </div>
      <p class="invite-sub invite-sub-error" id="admin-stats-error" hidden></p>

      <div id="admin-empty" class="lede" hidden>No requests recorded yet.</div>

      <div id="admin-tiles" class="grid grid-cols-2 gap-3 sm:grid-cols-3"></div>

      <section class="flex flex-col gap-3">
        <h2 class="text-sm font-semibold text-ink">Requests by day (last <span id="admin-window-days"></span> days)</h2>
        <div id="admin-chart-days"></div>
      </section>

      <section class="flex flex-col gap-3">
        <h2 class="text-sm font-semibold text-ink">Requests by tool</h2>
        <div id="admin-chart-tools" class="flex flex-col gap-2"></div>
      </section>

      <section class="flex flex-col gap-3">
        <h2 class="text-sm font-semibold text-ink">Top guideline ids</h2>
        <div id="admin-chart-guidelines" class="flex flex-col gap-2"></div>
      </section>
    </div>
  </main>`,
        { catalog: false, key: false, consent: false, paper: true },
      ),
    ),
  };
}

function tileHtml(label, value) {
  return `
  <div class="flex flex-col gap-1 rounded-sm border border-line bg-card px-4 py-3">
    <span class="text-xs text-muted">${escapeHtml(label)}</span>
    <span class="text-xl font-semibold text-ink">${escapeHtml(String(value))}</span>
  </div>`;
}

function daysChartSvg(requestsByDay) {
  const entries = Object.entries(requestsByDay || {});
  if (entries.length === 0) return "";
  const values = entries.map(([, v]) => Number(v) || 0);
  const max = Math.max(1, ...values);
  const w = 1000;
  const h = 160;
  const n = values.length;
  const xAt = (i) => (n === 1 ? 0 : (i / (n - 1)) * w);
  const yAt = (v) => h - (v / max) * h;
  const points = values.map((v, i) => `${xAt(i).toFixed(1)},${yAt(v).toFixed(1)}`);
  const linePath = `M ${points.join(" L ")}`;
  const areaPath = `M 0,${h} L ${points.join(" L ")} L ${w},${h} Z`;
  const gridY = [0, 0.25, 0.5, 0.75, 1].map((f) => h - f * h);
  const firstDate = entries[0][0];
  const lastDate = entries[entries.length - 1][0];
  return `
  <svg viewBox="0 0 ${w} ${h + 20}" class="w-full" style="max-height:200px" role="img" aria-label="Requests per day, ${escapeHtml(firstDate)} to ${escapeHtml(lastDate)}">
    ${gridY.map((y) => `<line x1="0" y1="${y}" x2="${w}" y2="${y}" class="stroke-line" stroke-width="1" opacity="0.6" />`).join("")}
    <path d="${areaPath}" class="fill-pip-soft" />
    <path d="${linePath}" class="stroke-pip" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
    <text x="0" y="${h + 16}" class="fill-muted" font-size="11">${escapeHtml(firstDate)}</text>
    <text x="${w}" y="${h + 16}" text-anchor="end" class="fill-muted" font-size="11">${escapeHtml(lastDate)}</text>
  </svg>`;
}

function rankedBarsHtml(rows, { emptyLabel }) {
  if (rows.length === 0) {
    return `<p class="text-sm text-muted">${escapeHtml(emptyLabel)}</p>`;
  }
  const max = Math.max(1, ...rows.map((r) => r.count));
  return rows
    .map(
      (r) => `
    <div class="flex items-center gap-3">
      <span class="w-48 shrink-0 truncate text-sm text-ink" title="${escapeHtml(r.label)}">${escapeHtml(r.label)}</span>
      <div class="h-3.5 flex-1 rounded-sm bg-line/40">
        <div class="h-3.5 rounded-sm bg-pip" style="width:${Math.max(2, Math.round((r.count / max) * 100))}%"></div>
      </div>
      <span class="w-12 shrink-0 text-right text-sm font-medium text-ink">${escapeHtml(String(r.count))}</span>
    </div>`,
    )
    .join("");
}

export function renderTelemetry(root) {
  const page = telemetryPage();
  setTitle(page.title);
  if (!root.querySelector('[data-ssr-page="admin-telemetry"]')) {
    root.innerHTML = page.body;
  }

  const loginView = document.getElementById("admin-login-view");
  const statsView = document.getElementById("admin-stats-view");
  const loginForm = document.getElementById("admin-login");
  const tokenInput = document.getElementById("admin-token");
  const toggleBtn = document.getElementById("admin-token-toggle");
  const loginSub = document.getElementById("admin-login-sub");
  const loginSubmit = document.getElementById("admin-login-submit");
  const footEl = document.getElementById("admin-login-foot");
  const logoutBtn = document.getElementById("admin-logout");
  const statsError = document.getElementById("admin-stats-error");
  const emptyEl = document.getElementById("admin-empty");
  const tilesEl = document.getElementById("admin-tiles");
  const windowDaysEl = document.getElementById("admin-window-days");
  const chartDaysEl = document.getElementById("admin-chart-days");
  const chartToolsEl = document.getElementById("admin-chart-tools");
  const chartGuidelinesEl = document.getElementById("admin-chart-guidelines");

  const LOGIN_SUB = "Paste the admin bearer token to view telemetry.";
  const REJECTED_SUB = "That token was rejected. Check it and try again.";

  let token = readToken();

  function showLogin(message) {
    clearToken();
    token = "";
    statsView.hidden = true;
    loginView.hidden = false;
    loginSub.textContent = message || LOGIN_SUB;
    loginSub.classList.toggle("invite-sub-error", Boolean(message));
    tokenInput.value = "";
    tokenInput.focus();
  }

  function onUnauthorized() {
    showLogin(REJECTED_SUB);
  }

  function renderStats(data) {
    windowDaysEl.textContent = String(data.window_days);
    emptyEl.hidden = data.total_requests > 0;

    tilesEl.innerHTML = [
      tileHtml("Total requests", data.total_requests),
      tileHtml("Unique callers", data.unique_keys),
      tileHtml("Accounts", data.accounts),
      tileHtml("Invites issued", data.invites),
      tileHtml("Waitlist", data.waitlist),
    ].join("");

    chartDaysEl.innerHTML = daysChartSvg(data.requests_by_day);

    const toolRows = Object.entries(data.requests_by_tool || {})
      .map(([label, count]) => ({ label, count }))
      .sort((a, b) => b.count - a.count);
    chartToolsEl.innerHTML = rankedBarsHtml(toolRows, { emptyLabel: "No tool calls recorded yet." });

    const guidelineRows = (data.top_guideline_ids || [])
      .map((row) => ({ label: row.id, count: row.count }))
      .sort((a, b) => b.count - a.count);
    chartGuidelinesEl.innerHTML = rankedBarsHtml(guidelineRows, {
      emptyLabel: "No guideline lookups recorded yet.",
    });
  }

  async function loadStats() {
    let response;
    try {
      response = await adminFetch(token, "/admin/stats");
    } catch {
      statsError.textContent = "Couldn't reach the server — try again.";
      statsError.hidden = false;
      return null;
    }
    if (response.status === 401) {
      onUnauthorized();
      return null;
    }
    if (!response.ok) {
      statsError.textContent = "Couldn't load telemetry — try again.";
      statsError.hidden = false;
      return null;
    }
    statsError.hidden = true;
    return response.json();
  }

  function showStats() {
    loginView.hidden = true;
    statsView.hidden = false;
  }

  toggleBtn.addEventListener("click", () => {
    const shown = toggleBtn.getAttribute("aria-pressed") === "true";
    tokenInput.type = shown ? "password" : "text";
    toggleBtn.setAttribute("aria-pressed", shown ? "false" : "true");
    toggleBtn.textContent = shown ? "Show" : "Hide";
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const candidate = tokenInput.value.trim();
    if (!candidate) return;
    setBusy(loginSubmit, true, "Sign in", "Signing in…");
    footEl.hidden = true;
    token = candidate;
    const data = await loadStats();
    setBusy(loginSubmit, false, "Sign in", "Signing in…");
    footEl.hidden = false;
    if (data === null) return;
    writeToken(token);
    showStats();
    renderStats(data);
  });

  logoutBtn.addEventListener("click", () => {
    showLogin();
  });

  if (token) {
    showStats();
    loadStats().then((data) => {
      if (data !== null) renderStats(data);
    });
  }
}
