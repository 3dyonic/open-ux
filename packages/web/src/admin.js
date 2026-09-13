import { adminFetch, clearToken, readToken, setBusy, writeToken } from "./admin-shared.js";
import { shell } from "./chrome.js";
import { emptyStateHtml } from "./empty-state.js";
import { escapeHtml, setPresent, setTitle, ssr } from "./util.js";

const PAGE_LIMIT = 100;
const CALLERS_LIMIT = 50;

const ADMIN_TITLE = "Admin — Open UX";
const ADMIN_DESCRIPTION = "Accounts admin: waitlist, approvals, and callers.";

export function adminPage() {
  return {
    title: ADMIN_TITLE,
    description: ADMIN_DESCRIPTION,
    path: "/admin",
    index: false,
    body: ssr(
      "admin",
      shell(
        `
  <main class="page">
    <div class="flex w-full flex-1 flex-col items-center justify-center" id="admin-login-view">
      <div class="invite-card" id="admin-login-card">
        <p class="invite-meta"><span class="pip" aria-hidden="true"></span>Admin · accounts</p>
        <h1 class="invite-title">Admin sign-in</h1>
        <p class="invite-sub" id="admin-login-sub">Paste the admin bearer token to view and approve the waitlist.</p>
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

    <div class="flex w-full flex-col gap-7" id="admin-table-card">
      <div class="flex items-center justify-between gap-4">
        <div class="flex flex-col gap-1">
          <p class="invite-meta"><span class="pip" aria-hidden="true"></span>Admin · accounts</p>
          <h1 class="page-title">Accounts</h1>
        </div>
        <button class="btn btn-outline btn-nav" type="button" id="admin-logout">Sign out</button>
      </div>

      <div class="flex items-center gap-5 border-b border-line" role="tablist">
        <button type="button" class="border-b-2 border-pip pb-2.5 text-sm font-semibold text-ink" data-tab-btn="waitlist" aria-selected="true">Waitlist</button>
        <button type="button" class="border-b-2 border-transparent pb-2.5 text-sm font-medium text-muted" data-tab-btn="approved" aria-selected="false">Approved</button>
      </div>

      <div id="admin-tab-waitlist"></div>
      <div id="admin-tab-approved"></div>
    </div>
  </main>`,
        { catalog: false, key: false, consent: false, paper: true, adminActive: "accounts" },
      ),
    ),
  };
}

function rowHtml(row) {
  const email = escapeHtml(row.email);
  const createdAt = escapeHtml(row.created_at);
  return `
  <div class="flex w-full flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-3.5 last:border-b-0" data-email="${email}">
    <div class="flex min-w-0 flex-1 flex-col gap-0.5">
      <span class="overflow-hidden text-ellipsis whitespace-nowrap text-sm font-medium text-ink">${email}</span>
      <span class="font-mono text-xs text-muted">${createdAt}</span>
    </div>
    <div class="flex shrink-0 items-center gap-2" data-row-actions>
      <button type="button" class="btn btn-primary btn-nav" data-approve>Approve</button>
    </div>
  </div>`;
}

function approvedRowHtml(row) {
  const email = escapeHtml(row.email);
  const createdAt = escapeHtml(row.created_at);
  const redeemed = Boolean(row.redeemed_at);
  const statusText = redeemed ? "Redeemed" : "Pending redemption";
  const statusMeta = redeemed
    ? `redeemed ${escapeHtml(row.redeemed_at)}`
    : `expires ${escapeHtml(row.expires_at)}`;
  return `
  <div class="flex w-full flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-3.5 last:border-b-0">
    <div class="flex min-w-0 flex-1 flex-col gap-0.5">
      <span class="overflow-hidden text-ellipsis whitespace-nowrap text-sm font-medium text-ink">${email}</span>
      <span class="font-mono text-xs text-muted">issued ${createdAt}</span>
    </div>
    <div class="flex shrink-0 items-center gap-2">
      <span class="status-chip${redeemed ? "" : " status-chip-neutral"}">${statusText}</span>
      <span class="font-mono text-xs text-muted">${statusMeta}</span>
    </div>
  </div>`;
}

function callerRowHtml(row) {
  const keyHash = escapeHtml(row.key_hash);
  return `
  <a class="flex w-full flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-3.5 text-left last:border-b-0 hover:bg-paper" href="/admin/telemetry/callers/${encodeURIComponent(row.key_hash)}">
    <span class="font-mono text-xs text-ink">${keyHash}</span>
    <span class="flex flex-wrap items-center gap-4 text-xs text-muted">
      <span>${row.session_count} session${row.session_count === 1 ? "" : "s"}</span>
      <span>${row.call_count} call${row.call_count === 1 ? "" : "s"}</span>
      <span class="font-mono">last ${escapeHtml(row.last_seen)}</span>
      ${row.top_target ? `<span class="font-mono">${escapeHtml(row.top_target)}</span>` : ""}
    </span>
  </a>`;
}

function rowErrorEl(message) {
  const el = document.createElement("p");
  el.className = "invite-sub invite-sub-error";
  el.setAttribute("data-row-error", "");
  el.textContent = message;
  return el;
}

async function approveRow(token, row, onUnauthorized) {
  const email = row.getAttribute("data-email") || "";
  const actions = row.querySelector("[data-row-actions]");
  const button = actions.querySelector("[data-approve]");
  if (!button) return;
  const existingError = actions.querySelector("[data-row-error]");
  if (existingError) existingError.remove();
  setBusy(button, true, "Approve", "Approving…");
  try {
    const response = await adminFetch(token, "/admin/invite/approve", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email }),
    });
    if (response.status === 401) {
      onUnauthorized();
      return;
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      setBusy(button, false, "Approve", "Approving…");
      actions.appendChild(rowErrorEl("Couldn’t approve this email — check it and try again."));
      return;
    }
    button.remove();
    const chip = document.createElement("span");
    chip.className = "status-chip";
    chip.textContent = "Approved";
    actions.appendChild(chip);
    if (data.redeem_url) {
      actions.insertAdjacentText("beforeend", " · ");
      const link = document.createElement("a");
      link.className = "invite-link";
      link.href = data.redeem_url;
      link.textContent = "redeem link";
      actions.appendChild(link);
    }
  } catch {
    setBusy(button, false, "Approve", "Approving…");
    actions.appendChild(rowErrorEl("Couldn’t reach the server — try again."));
  }
}

function tabPanelHtml({ errorId, listId, emptyId, pagerId, backToTopId, pagerMetaId, loadMoreId }) {
  return `
  <p class="invite-sub invite-sub-error" id="${errorId}"></p>
  <div class="list" id="${listId}"></div>
  <div id="${emptyId}"></div>
  <div class="pager" id="${pagerId}">
    <a class="back" href="#admin-table-card" id="${backToTopId}">↑ Back to top</a>
    <p class="pager-meta" id="${pagerMetaId}"></p>
    <button class="btn btn-outline" type="button" id="${loadMoreId}">Load more</button>
  </div>`;
}

// The Approved tab holds two structurally separate sections: invites
// (email-keyed) and callers (key_hash-keyed), never joined to each other.
// Each gets its own heading so they can't read as one merged list.
function invitesSectionHtml(panelHtml) {
  return `
  <section class="flex flex-col gap-3">
    <h2 class="text-sm font-semibold text-ink">Invites</h2>
    ${panelHtml}
  </section>`;
}

function callersSectionHtml() {
  return `
  <section class="flex flex-col gap-3 border-t border-line pt-6">
    <h2 class="text-sm font-semibold text-ink">Callers</h2>
    <p class="text-xs text-muted">Anonymized key_hash only, never joined to email. Sessions are a 30-minute idle-gap grouping — stateless HTTP has no real MCP session id.</p>
    <p class="invite-sub invite-sub-error" id="admin-callers-error"></p>
    <div class="list" id="admin-callers-list"></div>
    <div id="admin-callers-empty"></div>
    <div class="pager" id="admin-callers-pager">
      <p class="pager-meta" id="admin-callers-pager-meta"></p>
      <button class="btn btn-outline" type="button" id="admin-callers-load-more">Load more</button>
    </div>
  </section>`;
}

function makeListController({
  endpoint,
  rowHtml,
  panel,
  listEl,
  emptyEl,
  emptyMessage,
  errorEl,
  pagerEl,
  pagerMetaEl,
  loadMoreEl,
  getToken,
  onUnauthorized,
  limit = PAGE_LIMIT,
}) {
  let nextCursor = null;
  let loadedCount = 0;
  let errorMessage = "";

  // These four are the only children of `panel`, always processed together in
  // this fixed order — see setPresent's doc comment for why we insert/remove
  // rather than toggle `hidden`.
  function sync() {
    setPresent(errorEl, Boolean(errorMessage), panel);
    setPresent(listEl, loadedCount > 0, panel);
    setPresent(emptyEl, loadedCount === 0, panel);
    setPresent(pagerEl, Boolean(nextCursor), panel);
  }

  function reset() {
    listEl.innerHTML = "";
    emptyEl.innerHTML = "";
    errorMessage = "";
    errorEl.textContent = "";
    loadedCount = 0;
    nextCursor = null;
  }

  function render(data, { append }) {
    const items = Array.isArray(data.items) ? data.items : [];
    if (!append) listEl.innerHTML = "";
    listEl.innerHTML += items.map(rowHtml).join("");
    loadedCount += items.length;
    nextCursor = data.next_cursor || null;
    emptyEl.innerHTML = loadedCount === 0 ? emptyStateHtml(emptyMessage) : "";
    pagerMetaEl.textContent = `${loadedCount} loaded`;
    sync();
  }

  async function load({ append }) {
    const params = new URLSearchParams({ limit: String(limit) });
    if (append && nextCursor) params.set("before", nextCursor);
    let response;
    try {
      response = await adminFetch(getToken(), `${endpoint}?${params}`);
    } catch {
      errorMessage = "Couldn’t reach the server — try again.";
      errorEl.textContent = errorMessage;
      sync();
      return null;
    }
    if (response.status === 401) {
      onUnauthorized();
      return null;
    }
    if (!response.ok) {
      errorMessage = "Couldn’t load this list — try again.";
      errorEl.textContent = errorMessage;
      sync();
      return null;
    }
    errorMessage = "";
    return response.json();
  }

  loadMoreEl.addEventListener("click", async () => {
    setBusy(loadMoreEl, true, "Load more", "Loading…");
    const data = await load({ append: true });
    if (data !== null) render(data, { append: true });
    setBusy(loadMoreEl, false, "Load more", "Loading…");
  });

  return {
    async loadFirst() {
      reset();
      sync();
      const data = await load({ append: false });
      if (data !== null) render(data, { append: false });
      else sync();
      return data;
    },
  };
}

export function renderAdmin(root) {
  const page = adminPage();
  setTitle(page.title);
  if (!root.querySelector('[data-ssr-page="admin"]')) {
    root.innerHTML = page.body;
  }

  const mainEl = document.querySelector("main.page");
  const loginView = document.getElementById("admin-login-view");
  const tableCard = document.getElementById("admin-table-card");
  const loginForm = document.getElementById("admin-login");
  const tokenInput = document.getElementById("admin-token");
  const toggleBtn = document.getElementById("admin-token-toggle");
  const loginSub = document.getElementById("admin-login-sub");
  const loginSubmit = document.getElementById("admin-login-submit");
  const footEl = document.getElementById("admin-login-foot");
  const logoutBtn = document.getElementById("admin-logout");

  const waitlistPanel = document.getElementById("admin-tab-waitlist");
  const approvedPanel = document.getElementById("admin-tab-approved");
  waitlistPanel.innerHTML = tabPanelHtml({
    errorId: "admin-table-error",
    listId: "admin-waitlist-list",
    emptyId: "admin-empty",
    pagerId: "admin-pager",
    backToTopId: "admin-back-to-top",
    pagerMetaId: "admin-pager-meta",
    loadMoreId: "admin-load-more",
  });
  approvedPanel.innerHTML =
    invitesSectionHtml(
      tabPanelHtml({
        errorId: "admin-approved-error",
        listId: "admin-approved-list",
        emptyId: "admin-approved-empty",
        pagerId: "admin-approved-pager",
        backToTopId: "admin-approved-back-to-top",
        pagerMetaId: "admin-approved-pager-meta",
        loadMoreId: "admin-approved-load-more",
      }),
    ) + callersSectionHtml();
  const waitlistList = document.getElementById("admin-waitlist-list");

  const tabButtons = Array.from(document.querySelectorAll("[data-tab-btn]"));
  const tabPanels = { waitlist: waitlistPanel, approved: approvedPanel };
  const tabsParent = waitlistPanel.parentNode;

  const LOGIN_SUB = "Paste the admin bearer token to view and approve the waitlist.";
  const REJECTED_SUB = "That token was rejected. Check it and try again.";

  let token = readToken();
  const loadedTabs = new Set();

  function onUnauthorized() {
    showLogin(REJECTED_SUB);
  }

  const waitlistController = makeListController({
    endpoint: "/admin/invite/waitlist",
    rowHtml,
    panel: waitlistPanel,
    listEl: waitlistList,
    emptyEl: document.getElementById("admin-empty"),
    emptyMessage: "No one on the waitlist yet.",
    errorEl: document.getElementById("admin-table-error"),
    pagerEl: document.getElementById("admin-pager"),
    pagerMetaEl: document.getElementById("admin-pager-meta"),
    loadMoreEl: document.getElementById("admin-load-more"),
    getToken: () => token,
    onUnauthorized,
  });

  const approvedController = makeListController({
    endpoint: "/admin/invite/approved",
    rowHtml: approvedRowHtml,
    panel: document.getElementById("admin-approved-list").parentNode,
    listEl: document.getElementById("admin-approved-list"),
    emptyEl: document.getElementById("admin-approved-empty"),
    emptyMessage: "No approved invites yet.",
    errorEl: document.getElementById("admin-approved-error"),
    pagerEl: document.getElementById("admin-approved-pager"),
    pagerMetaEl: document.getElementById("admin-approved-pager-meta"),
    loadMoreEl: document.getElementById("admin-approved-load-more"),
    getToken: () => token,
    onUnauthorized,
  });

  const callersController = makeListController({
    endpoint: "/admin/sessions",
    rowHtml: callerRowHtml,
    panel: document.getElementById("admin-callers-list").parentNode,
    listEl: document.getElementById("admin-callers-list"),
    emptyEl: document.getElementById("admin-callers-empty"),
    emptyMessage: "No callers recorded yet.",
    errorEl: document.getElementById("admin-callers-error"),
    pagerEl: document.getElementById("admin-callers-pager"),
    pagerMetaEl: document.getElementById("admin-callers-pager-meta"),
    loadMoreEl: document.getElementById("admin-callers-load-more"),
    getToken: () => token,
    onUnauthorized,
    limit: CALLERS_LIMIT,
  });

  const controllers = {
    waitlist: [waitlistController],
    approved: [approvedController, callersController],
  };

  function showLogin(message) {
    clearToken();
    token = "";
    setPresent(tableCard, false, mainEl);
    setPresent(loginView, true, mainEl);
    loginSub.textContent = message || LOGIN_SUB;
    loginSub.classList.toggle("invite-sub-error", Boolean(message));
    tokenInput.value = "";
    tokenInput.focus();
  }

  function setActiveTab(tab) {
    for (const btn of tabButtons) {
      const isActive = btn.dataset.tabBtn === tab;
      btn.setAttribute("aria-selected", isActive ? "true" : "false");
      btn.classList.toggle("border-pip", isActive);
      btn.classList.toggle("text-ink", isActive);
      btn.classList.toggle("font-semibold", isActive);
      btn.classList.toggle("border-transparent", !isActive);
      btn.classList.toggle("text-muted", !isActive);
      btn.classList.toggle("font-medium", !isActive);
    }
    for (const [name, panel] of Object.entries(tabPanels)) {
      setPresent(panel, name === tab, tabsParent);
    }
    if (!loadedTabs.has(tab)) {
      loadedTabs.add(tab);
      for (const controller of controllers[tab]) controller.loadFirst();
    }
  }

  function showTable() {
    setPresent(loginView, false, mainEl);
    setPresent(tableCard, true, mainEl);
    loadedTabs.clear();
    setActiveTab("waitlist");
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
    const data = await waitlistController.loadFirst();
    setBusy(loginSubmit, false, "Sign in", "Signing in…");
    setPresent(footEl, true, loginForm);
    if (data === null) {
      token = "";
      return;
    }
    writeToken(token);
    setPresent(loginView, false, mainEl);
    setPresent(tableCard, true, mainEl);
    loadedTabs.clear();
    loadedTabs.add("waitlist");
    setActiveTab("waitlist");
  });

  logoutBtn.addEventListener("click", () => {
    showLogin();
  });

  for (const btn of tabButtons) {
    btn.addEventListener("click", () => setActiveTab(btn.dataset.tabBtn));
  }

  waitlistList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-approve]");
    if (!button) return;
    const row = button.closest("[data-email]");
    if (!row) return;
    approveRow(token, row, onUnauthorized);
  });

  setPresent(tableCard, false, mainEl);
  if (token) {
    showTable();
  } else {
    setPresent(loginView, true, mainEl);
  }
}
