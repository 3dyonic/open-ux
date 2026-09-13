import { shell } from "./chrome.js";
import { emptyStateHtml } from "./empty-state.js";
import { escapeHtml, setPresent, setTitle, ssr } from "./util.js";

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

    <div class="flex w-full flex-col gap-7" id="admin-stats-view">
      <div class="flex items-center justify-between gap-4">
        <div class="flex flex-col gap-1">
          <p class="invite-meta"><span class="pip" aria-hidden="true"></span>Admin · telemetry</p>
          <h1 class="page-title">Telemetry</h1>
        </div>
        <button class="btn btn-outline btn-nav" type="button" id="admin-logout">Sign out</button>
      </div>
      <p class="invite-sub invite-sub-error" id="admin-stats-error"></p>

      <div id="admin-empty"></div>

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

      <section class="flex flex-col gap-3">
        <h2 class="text-sm font-semibold text-ink">Callers</h2>
        <p class="text-xs text-muted">Anonymized key_hash only, never joined to email. Sessions are a 30-minute idle-gap grouping — stateless HTTP has no real MCP session id.</p>
        <p class="invite-sub invite-sub-error" id="admin-callers-error"></p>
        <div class="list" id="admin-callers-list"></div>
        <div id="admin-callers-empty"></div>
        <div class="pager" id="admin-callers-pager">
          <p class="pager-meta" id="admin-callers-pager-meta"></p>
          <button class="btn btn-outline" type="button" id="admin-callers-load-more">Load more</button>
        </div>
      </section>
    </div>
  </main>`,
        { catalog: false, key: false, consent: false, paper: true, adminActive: "telemetry" },
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
    return emptyStateHtml(emptyLabel);
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

function stepsHtml(steps) {
  return `
  <ol class="flex flex-col gap-1 border-t border-line py-2 pl-4 text-xs">
    ${steps
      .map(
        (s, i) => `
    <li class="flex flex-wrap items-center gap-2">
      <span class="text-muted">${i + 1}.</span>
      <span class="font-mono font-medium text-pip">${escapeHtml(s.tool)}</span>
      ${s.target_type ? `<span class="font-mono text-muted">${escapeHtml(s.target_type)}=${escapeHtml(s.target_id || "")}</span>` : ""}
      ${s.verdicts ? `<span class="font-mono text-muted">${escapeHtml(JSON.stringify(s.verdicts))}</span>` : ""}
      <span class="ml-auto font-mono text-muted">${escapeHtml(s.created_at)}</span>
    </li>`,
      )
      .join("")}
  </ol>`;
}

function sessionRowHtml(session) {
  const email = escapeHtml(session.session_id);
  return `
  <div class="border-t border-line" data-session-id="${email}">
    <button type="button" class="flex w-full items-center justify-between gap-3 py-2.5 pl-4 text-left" data-session-toggle aria-expanded="false">
      <span class="font-mono text-xs text-ink">${email}</span>
      <span class="flex items-center gap-3 text-xs text-muted">
        <span>${session.call_count} call${session.call_count === 1 ? "" : "s"}</span>
        <span class="font-mono">${escapeHtml(session.started_at)}</span>
        <span data-chevron>▸</span>
      </span>
    </button>
    <div data-session-steps></div>
  </div>`;
}

function callerRowHtml(row) {
  const keyHash = escapeHtml(row.key_hash);
  return `
  <div class="border-b border-line last:border-b-0" data-key-hash="${keyHash}">
    <button type="button" class="flex w-full flex-wrap items-center justify-between gap-3 px-5 py-3.5 text-left" data-caller-toggle aria-expanded="false">
      <span class="font-mono text-xs text-ink">${keyHash}</span>
      <span class="flex flex-wrap items-center gap-4 text-xs text-muted">
        <span>${row.session_count} session${row.session_count === 1 ? "" : "s"}</span>
        <span>${row.call_count} call${row.call_count === 1 ? "" : "s"}</span>
        <span class="font-mono">last ${escapeHtml(row.last_seen)}</span>
        ${row.top_target ? `<span class="font-mono">${escapeHtml(row.top_target)}</span>` : ""}
        <span data-chevron>▸</span>
      </span>
    </button>
    <div data-caller-sessions></div>
  </div>`;
}

export function renderTelemetry(root) {
  const page = telemetryPage();
  setTitle(page.title);
  if (!root.querySelector('[data-ssr-page="admin-telemetry"]')) {
    root.innerHTML = page.body;
  }

  const mainEl = document.querySelector("main.page");
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
  const callersList = document.getElementById("admin-callers-list");
  const callersEmpty = document.getElementById("admin-callers-empty");
  const callersError = document.getElementById("admin-callers-error");
  const callersPager = document.getElementById("admin-callers-pager");
  const callersPagerMeta = document.getElementById("admin-callers-pager-meta");
  const callersLoadMore = document.getElementById("admin-callers-load-more");
  const callersPanel = callersList.parentNode;

  // statsError and emptyEl are the only two banners that sit before the
  // always-present tilesEl; inserting each right before it, in this order,
  // is what keeps [statsError, emptyEl, tilesEl] in the correct visual order
  // however many times sync() below re-runs (see setPresent's doc comment).
  function syncBanners({ hasError, isEmpty }) {
    setPresent(statsError, hasError, statsView, tilesEl);
    setPresent(emptyEl, isEmpty, statsView, tilesEl);
  }

  const LOGIN_SUB = "Paste the admin bearer token to view telemetry.";
  const REJECTED_SUB = "That token was rejected. Check it and try again.";

  let token = readToken();

  function showLogin(message) {
    clearToken();
    token = "";
    setPresent(statsView, false, mainEl);
    setPresent(loginView, true, mainEl);
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
    emptyEl.innerHTML = data.total_requests === 0 ? emptyStateHtml("No requests recorded yet.") : "";
    syncBanners({ hasError: false, isEmpty: data.total_requests === 0 });

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

  const CALLERS_LIMIT = 50;
  let callersNextCursor = null;
  let callersLoadedCount = 0;
  const sessionCache = new Map(); // key_hash -> sessions array, so re-expanding doesn't refetch

  function syncCallers() {
    setPresent(callersError, Boolean(callersError.textContent), callersPanel);
    setPresent(callersList, callersLoadedCount > 0, callersPanel);
    setPresent(callersEmpty, callersLoadedCount === 0, callersPanel);
    setPresent(callersPager, Boolean(callersNextCursor), callersPanel);
  }

  function renderCallers(data, { append }) {
    const items = Array.isArray(data.items) ? data.items : [];
    if (!append) callersList.innerHTML = "";
    callersList.innerHTML += items.map(callerRowHtml).join("");
    callersLoadedCount += items.length;
    callersNextCursor = data.next_cursor || null;
    callersEmpty.innerHTML = callersLoadedCount === 0 ? emptyStateHtml("No callers recorded yet.") : "";
    callersPagerMeta.textContent = `${callersLoadedCount} loaded`;
    syncCallers();
  }

  async function loadCallers({ append }) {
    const params = new URLSearchParams({ limit: String(CALLERS_LIMIT) });
    if (append && callersNextCursor) params.set("before", callersNextCursor);
    let response;
    try {
      response = await adminFetch(token, `/admin/sessions?${params}`);
    } catch {
      callersError.textContent = "Couldn’t reach the server — try again.";
      syncCallers();
      return null;
    }
    if (response.status === 401) {
      onUnauthorized();
      return null;
    }
    if (!response.ok) {
      callersError.textContent = "Couldn’t load callers — try again.";
      syncCallers();
      return null;
    }
    callersError.textContent = "";
    return response.json();
  }

  async function loadCallersFirst() {
    callersList.innerHTML = "";
    callersEmpty.innerHTML = "";
    callersError.textContent = "";
    callersLoadedCount = 0;
    callersNextCursor = null;
    sessionCache.clear();
    syncCallers();
    const data = await loadCallers({ append: false });
    if (data !== null) renderCallers(data, { append: false });
  }

  callersLoadMore.addEventListener("click", async () => {
    setBusy(callersLoadMore, true, "Load more", "Loading…");
    const data = await loadCallers({ append: true });
    if (data !== null) renderCallers(data, { append: true });
    setBusy(callersLoadMore, false, "Load more", "Loading…");
  });

  callersList.addEventListener("click", async (event) => {
    const sessionToggle = event.target.closest("[data-session-toggle]");
    if (sessionToggle) {
      const sessionRow = sessionToggle.closest("[data-session-id]");
      const stepsEl = sessionRow.querySelector("[data-session-steps]");
      const expanded = sessionToggle.getAttribute("aria-expanded") === "true";
      sessionToggle.setAttribute("aria-expanded", expanded ? "false" : "true");
      sessionToggle.querySelector("[data-chevron]").textContent = expanded ? "▸" : "▾";
      stepsEl.innerHTML = expanded ? "" : stepsEl.dataset.pendingHtml || "";
      return;
    }
    const callerToggle = event.target.closest("[data-caller-toggle]");
    if (!callerToggle) return;
    const callerRow = callerToggle.closest("[data-key-hash]");
    const keyHash = callerRow.getAttribute("data-key-hash");
    const sessionsEl = callerRow.querySelector("[data-caller-sessions]");
    const expanded = callerToggle.getAttribute("aria-expanded") === "true";
    if (expanded) {
      callerToggle.setAttribute("aria-expanded", "false");
      callerToggle.querySelector("[data-chevron]").textContent = "▸";
      sessionsEl.innerHTML = "";
      return;
    }
    callerToggle.setAttribute("aria-expanded", "true");
    callerToggle.querySelector("[data-chevron]").textContent = "▾";
    if (sessionCache.has(keyHash)) {
      sessionsEl.innerHTML = sessionCache.get(keyHash).map(sessionRowHtml).join("");
      return;
    }
    sessionsEl.innerHTML = `<p class="pl-4 py-2 text-xs text-muted">Loading…</p>`;
    let response;
    try {
      response = await adminFetch(token, `/admin/sessions/${encodeURIComponent(keyHash)}?limit=${CALLERS_LIMIT}`);
    } catch {
      sessionsEl.innerHTML = `<p class="pl-4 py-2 text-xs text-muted">Couldn’t reach the server — try again.</p>`;
      return;
    }
    if (response.status === 401) {
      onUnauthorized();
      return;
    }
    if (!response.ok) {
      sessionsEl.innerHTML = `<p class="pl-4 py-2 text-xs text-muted">Couldn’t load sessions — try again.</p>`;
      return;
    }
    const data = await response.json();
    const sessions = Array.isArray(data.items) ? data.items : [];
    sessionCache.set(keyHash, sessions);
    sessionsEl.innerHTML = sessions.map(sessionRowHtml).join("");
    // Steps are pre-fetched with the session; stash their HTML for instant
    // expand/collapse instead of fetching per session.
    sessionsEl.querySelectorAll("[data-session-id]").forEach((row, i) => {
      row.querySelector("[data-session-steps]").dataset.pendingHtml = stepsHtml(sessions[i].steps);
    });
  });

  async function loadStats() {
    let response;
    try {
      response = await adminFetch(token, "/admin/stats");
    } catch {
      statsError.textContent = "Couldn't reach the server — try again.";
      syncBanners({ hasError: true, isEmpty: false });
      return null;
    }
    if (response.status === 401) {
      onUnauthorized();
      return null;
    }
    if (!response.ok) {
      statsError.textContent = "Couldn't load telemetry — try again.";
      syncBanners({ hasError: true, isEmpty: false });
      return null;
    }
    return response.json();
  }

  function showStats() {
    setPresent(loginView, false, mainEl);
    setPresent(statsView, true, mainEl);
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
    setPresent(footEl, false, loginForm);
    token = candidate;
    const data = await loadStats();
    setBusy(loginSubmit, false, "Sign in", "Signing in…");
    setPresent(footEl, true, loginForm);
    if (data === null) return;
    writeToken(token);
    showStats();
    renderStats(data);
    loadCallersFirst();
  });

  logoutBtn.addEventListener("click", () => {
    showLogin();
  });

  setPresent(statsView, false, mainEl);
  syncBanners({ hasError: false, isEmpty: false });
  syncCallers();
  if (token) {
    showStats();
    loadStats().then((data) => {
      if (data !== null) renderStats(data);
    });
    loadCallersFirst();
  } else {
    setPresent(loginView, true, mainEl);
  }
}
