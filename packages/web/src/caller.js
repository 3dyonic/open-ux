import { adminFetch, clearToken, readToken, setBusy, writeToken } from "./admin-shared.js";
import { shell } from "./chrome.js";
import { emptyStateHtml } from "./empty-state.js";
import { escapeHtml, setPresent, setTitle, ssr } from "./util.js";

const CALLER_TITLE = "Caller — Open UX";
const CALLER_DESCRIPTION = "One caller's telemetry sessions.";
const SESSIONS_LIMIT = 50;

export function callerPage() {
  return {
    title: CALLER_TITLE,
    description: CALLER_DESCRIPTION,
    path: "/admin/telemetry/callers",
    index: false,
    body: ssr(
      "admin-caller",
      shell(
        `
  <main class="page">
    <div class="flex w-full flex-1 flex-col items-center justify-center" id="admin-login-view">
      <div class="invite-card" id="admin-login-card">
        <p class="invite-meta"><span class="pip" aria-hidden="true"></span>Admin · accounts</p>
        <h1 class="invite-title">Admin sign-in</h1>
        <p class="invite-sub" id="admin-login-sub">Paste the admin bearer token to view this caller.</p>
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

    <div class="flex w-full flex-col gap-7" id="admin-caller-view">
      <a class="back" href="/admin">← Back to accounts</a>
      <div class="flex flex-col gap-1">
        <p class="invite-meta"><span class="pip" aria-hidden="true"></span>Admin · Accounts · Callers</p>
        <h1 class="page-title font-mono" id="admin-caller-title"></h1>
        <p class="lede" id="admin-caller-summary"></p>
      </div>
      <p class="invite-sub invite-sub-error" id="admin-caller-error"></p>
      <div id="admin-caller-empty"></div>
      <div class="list" id="admin-caller-sessions"></div>
      <div class="pager" id="admin-caller-pager">
        <p class="pager-meta" id="admin-caller-pager-meta"></p>
        <button class="btn btn-outline" type="button" id="admin-caller-load-more">Load more</button>
      </div>
    </div>
  </main>`,
        { catalog: false, key: false, consent: false, paper: true, adminActive: "accounts" },
      ),
    ),
  };
}

function flagsHtml(flags) {
  if (!flags) return "";
  const on = Object.entries(flags)
    .filter(([, v]) => v)
    .map(([k]) => `+${k.replace(/^include_/, "")}`);
  const off = Object.entries(flags)
    .filter(([, v]) => !v)
    .map(([k]) => `-${k.replace(/^include_/, "")}`);
  const text = [...on, ...off].join(" ");
  return text ? `<span class="font-mono text-muted">${escapeHtml(text)}</span>` : "";
}

function resultIdsHtml(ids) {
  if (!ids || ids.length === 0) return "";
  return `<span class="font-mono text-muted" title="${escapeHtml(ids.join(", "))}">${escapeHtml(ids.join(", "))}</span>`;
}

function verdictsHtml(verdicts) {
  if (!verdicts) return "";
  const badges = [];
  if (typeof verdicts.helpful === "boolean") {
    badges.push(
      verdicts.helpful
        ? `<span class="status-chip">helpful</span>`
        : `<span class="status-chip status-chip-neutral">not helpful</span>`,
    );
  }
  const rest = Object.fromEntries(
    Object.entries(verdicts).filter(([k]) => k !== "helpful"),
  );
  if (Object.keys(rest).length > 0) {
    badges.push(`<span class="font-mono text-muted">${escapeHtml(JSON.stringify(rest))}</span>`);
  }
  return badges.join("");
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
      ${flagsHtml(s.req_flags)}
      ${typeof s.result_count === "number" ? `<span class="font-mono text-muted">→ ${s.result_count} result${s.result_count === 1 ? "" : "s"}</span>` : ""}
      ${resultIdsHtml(s.guideline_ids || s.result_ids)}
      ${verdictsHtml(s.verdicts)}
      <span class="ml-auto font-mono text-muted">${escapeHtml(s.created_at)}</span>
    </li>`,
      )
      .join("")}
  </ol>`;
}

function sessionRowHtml(session) {
  const id = escapeHtml(session.session_id);
  return `
  <div class="border-b border-line px-5 py-3.5 last:border-b-0" data-session-id="${id}">
    <button type="button" class="flex w-full flex-wrap items-center justify-between gap-3 text-left" data-session-toggle aria-expanded="false">
      <span class="font-mono text-xs text-ink">${escapeHtml(session.started_at)}</span>
      <span class="flex flex-wrap items-center gap-4 text-xs text-muted">
        <span>${session.duration_seconds}s</span>
        <span>${session.call_count} call${session.call_count === 1 ? "" : "s"}</span>
        <span class="max-w-[360px] truncate font-mono" title="${escapeHtml(session.tool_sequence)}">${escapeHtml(session.tool_sequence)}</span>
        ${session.target_id ? `<span class="font-mono text-pip">${escapeHtml(session.target_id)}</span>` : ""}
        <span data-chevron>▸</span>
      </span>
    </button>
    <div data-session-steps></div>
  </div>`;
}

export function renderCaller(root) {
  const keyHash = decodeURIComponent(
    location.pathname.replace(/^\/admin\/telemetry\/callers\//, "").replace(/\/$/, ""),
  );

  const page = callerPage();
  setTitle(`Caller ${keyHash} — Open UX`);
  if (!root.querySelector('[data-ssr-page="admin-caller"]')) {
    root.innerHTML = page.body;
  }

  const mainEl = document.querySelector("main.page");
  const loginView = document.getElementById("admin-login-view");
  const callerView = document.getElementById("admin-caller-view");
  const loginForm = document.getElementById("admin-login");
  const tokenInput = document.getElementById("admin-token");
  const toggleBtn = document.getElementById("admin-token-toggle");
  const loginSub = document.getElementById("admin-login-sub");
  const loginSubmit = document.getElementById("admin-login-submit");
  const footEl = document.getElementById("admin-login-foot");
  const titleEl = document.getElementById("admin-caller-title");
  const summaryEl = document.getElementById("admin-caller-summary");
  const errorEl = document.getElementById("admin-caller-error");
  const emptyEl = document.getElementById("admin-caller-empty");
  const sessionsList = document.getElementById("admin-caller-sessions");
  const pagerEl = document.getElementById("admin-caller-pager");
  const pagerMetaEl = document.getElementById("admin-caller-pager-meta");
  const loadMoreEl = document.getElementById("admin-caller-load-more");

  const LOGIN_SUB = "Paste the admin bearer token to view this caller.";
  const REJECTED_SUB = "That token was rejected. Check it and try again.";

  let token = readToken();
  let nextCursor = null;
  let loadedCount = 0;
  const loadedSessionsById = new Map();

  titleEl.textContent = `Caller ${keyHash}`;

  function showLogin(message) {
    clearToken();
    token = "";
    setPresent(callerView, false, mainEl);
    setPresent(loginView, true, mainEl);
    loginSub.textContent = message || LOGIN_SUB;
    loginSub.classList.toggle("invite-sub-error", Boolean(message));
    tokenInput.value = "";
    tokenInput.focus();
  }

  function onUnauthorized() {
    showLogin(REJECTED_SUB);
  }

  // errorEl, sessionsList, emptyEl, pagerEl are the only children of
  // callerView after the header block, always processed together in this
  // fixed order — see setPresent's doc comment in util.js.
  function sync() {
    setPresent(errorEl, Boolean(errorEl.textContent), callerView);
    setPresent(sessionsList, loadedCount > 0, callerView);
    setPresent(emptyEl, loadedCount === 0, callerView);
    setPresent(pagerEl, Boolean(nextCursor), callerView);
  }

  function renderSummary(summary) {
    if (summary.call_count === 0) {
      summaryEl.textContent = "No calls recorded yet for this caller.";
      return;
    }
    const parts = [
      `${summary.session_count} session${summary.session_count === 1 ? "" : "s"}`,
      `${summary.call_count} call${summary.call_count === 1 ? "" : "s"}`,
      `first seen ${summary.first_seen}`,
      `last seen ${summary.last_seen}`,
    ];
    let text = parts.join(" · ") + ".";
    if (summary.top_target) {
      text += ` Called ${summary.top_target} most often.`;
    }
    summaryEl.textContent = text;
  }

  function renderSessions(data, { append }) {
    const items = Array.isArray(data.items) ? data.items : [];
    for (const session of items) loadedSessionsById.set(session.session_id, session);
    if (!append) sessionsList.innerHTML = "";
    sessionsList.innerHTML += items.map(sessionRowHtml).join("");
    loadedCount += items.length;
    nextCursor = data.next_cursor || null;
    emptyEl.innerHTML = loadedCount === 0 ? emptyStateHtml("No sessions recorded yet.") : "";
    pagerMetaEl.textContent = `${loadedCount} loaded`;
    sync();
  }

  async function loadSessions({ append }) {
    const params = new URLSearchParams({ limit: String(SESSIONS_LIMIT) });
    if (append && nextCursor) params.set("before", nextCursor);
    let response;
    try {
      response = await adminFetch(token, `/admin/sessions/${encodeURIComponent(keyHash)}?${params}`);
    } catch {
      errorEl.textContent = "Couldn’t reach the server — try again.";
      sync();
      return null;
    }
    if (response.status === 401) {
      onUnauthorized();
      return null;
    }
    if (!response.ok) {
      errorEl.textContent = "Couldn’t load this caller — try again.";
      sync();
      return null;
    }
    errorEl.textContent = "";
    return response.json();
  }

  async function loadFirst() {
    sessionsList.innerHTML = "";
    emptyEl.innerHTML = "";
    errorEl.textContent = "";
    loadedCount = 0;
    nextCursor = null;
    sync();
    const data = await loadSessions({ append: false });
    if (data === null) return;
    renderSummary(data.summary);
    renderSessions(data, { append: false });
  }

  loadMoreEl.addEventListener("click", async () => {
    setBusy(loadMoreEl, true, "Load more", "Loading…");
    const data = await loadSessions({ append: true });
    if (data !== null) renderSessions(data, { append: true });
    setBusy(loadMoreEl, false, "Load more", "Loading…");
  });

  sessionsList.addEventListener("click", (event) => {
    const toggle = event.target.closest("[data-session-toggle]");
    if (!toggle) return;
    const row = toggle.closest("[data-session-id]");
    const stepsEl = row.querySelector("[data-session-steps]");
    const sessionId = row.getAttribute("data-session-id");
    const expanded = toggle.getAttribute("aria-expanded") === "true";
    toggle.setAttribute("aria-expanded", expanded ? "false" : "true");
    toggle.querySelector("[data-chevron]").textContent = expanded ? "▸" : "▾";
    if (expanded) {
      stepsEl.innerHTML = "";
      return;
    }
    const session = loadedSessionsById.get(sessionId);
    stepsEl.innerHTML = session ? stepsHtml(session.steps) : "";
  });

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
    const data = await loadSessions({ append: false });
    setBusy(loginSubmit, false, "Sign in", "Signing in…");
    setPresent(footEl, true, loginForm);
    if (data === null) {
      token = "";
      return;
    }
    writeToken(token);
    setPresent(loginView, false, mainEl);
    setPresent(callerView, true, mainEl);
    renderSummary(data.summary);
    renderSessions(data, { append: false });
  });

  setPresent(callerView, false, mainEl);
  sync();
  if (token) {
    setPresent(loginView, false, mainEl);
    setPresent(callerView, true, mainEl);
    loadFirst();
  } else {
    setPresent(loginView, true, mainEl);
  }
}
