import { shell } from "./chrome.js";
import { escapeHtml, setTitle, ssr } from "./util.js";

const TOKEN_KEY = "open_ux_admin_token";
const PAGE_LIMIT = 100;

const ADMIN_TITLE = "Admin — Open UX";
const ADMIN_DESCRIPTION = "Invite waitlist admin.";

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
    // sessionStorage unavailable (private mode, etc.) — token just won't survive a reload.
  }
}

function clearToken() {
  try {
    sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    // nothing to clear
  }
}

async function adminFetch(token, path, options = {}) {
  const headers = { ...(options.headers || {}), Authorization: `Bearer ${token}` };
  const response = await fetch(path, { ...options, headers });
  return response;
}

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
        <p class="invite-meta"><span class="pip" aria-hidden="true"></span>Admin · invite waitlist</p>
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

    <div class="flex w-full flex-col gap-7" id="admin-table-card" hidden>
      <div class="flex items-center justify-between gap-4">
        <div class="flex flex-col gap-1">
          <p class="invite-meta"><span class="pip" aria-hidden="true"></span>Admin · invites</p>
          <h1 class="page-title">Invites</h1>
        </div>
        <button class="btn btn-outline btn-nav" type="button" id="admin-logout">Sign out</button>
      </div>

      <div class="flex items-center gap-5 border-b border-line" role="tablist">
        <button type="button" class="border-b-2 border-pip pb-2.5 text-sm font-semibold text-ink" data-tab-btn="waitlist" aria-selected="true">Waitlist</button>
        <button type="button" class="border-b-2 border-transparent pb-2.5 text-sm font-medium text-muted" data-tab-btn="approved" aria-selected="false">Approved</button>
      </div>

      <div id="admin-tab-waitlist">
        <p class="invite-sub invite-sub-error" id="admin-table-error" hidden></p>
        <div class="list" id="admin-waitlist-list"></div>
        <p class="lede" id="admin-empty" hidden>No one on the waitlist yet.</p>
        <div class="pager" id="admin-pager" hidden>
          <a class="back" href="#admin-table-card" id="admin-back-to-top">↑ Back to top</a>
          <p class="pager-meta" id="admin-pager-meta"></p>
          <button class="btn btn-outline" type="button" id="admin-load-more">Load more</button>
        </div>
      </div>

      <div id="admin-tab-approved" hidden>
        <p class="invite-sub invite-sub-error" id="admin-approved-error" hidden></p>
        <div class="list" id="admin-approved-list"></div>
        <p class="lede" id="admin-approved-empty" hidden>No approved invites yet.</p>
        <div class="pager" id="admin-approved-pager" hidden>
          <a class="back" href="#admin-table-card" id="admin-approved-back-to-top">↑ Back to top</a>
          <p class="pager-meta" id="admin-approved-pager-meta"></p>
          <button class="btn btn-outline" type="button" id="admin-approved-load-more">Load more</button>
        </div>
      </div>
    </div>
  </main>`,
        { catalog: false, key: false, consent: false, paper: true, adminActive: "invites" },
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
    <div class="flex shrink-0 items-center gap-2">
      <button type="button" class="btn btn-primary btn-nav" data-approve>Approve</button>
      <span class="status-chip" data-approved hidden>Approved</span>
      <p class="invite-sub invite-sub-error" data-row-error hidden></p>
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

async function approveRow(token, row, onUnauthorized) {
  const email = row.getAttribute("data-email") || "";
  const button = row.querySelector("[data-approve]");
  const chip = row.querySelector("[data-approved]");
  const errorEl = row.querySelector("[data-row-error]");
  if (!button) return;
  errorEl.hidden = true;
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
      errorEl.textContent =
        "Couldn’t approve this email — check it and try again.";
      errorEl.hidden = false;
      return;
    }
    button.hidden = true;
    chip.hidden = false;
    if (data.redeem_url) {
      const link = document.createElement("a");
      link.className = "invite-link";
      link.href = data.redeem_url;
      link.textContent = "redeem link";
      chip.insertAdjacentText("afterend", " · ");
      chip.insertAdjacentElement("afterend", link);
    }
  } catch {
    setBusy(button, false, "Approve", "Approving…");
    errorEl.textContent = "Couldn’t reach the server — try again.";
    errorEl.hidden = false;
  }
}

function makeListController({
  endpoint,
  rowHtml,
  listEl,
  emptyEl,
  errorEl,
  pagerEl,
  pagerMetaEl,
  loadMoreEl,
  getToken,
  onUnauthorized,
}) {
  let nextCursor = null;
  let loadedCount = 0;

  function reset() {
    listEl.innerHTML = "";
    errorEl.hidden = true;
    loadedCount = 0;
    nextCursor = null;
  }

  function render(data, { append }) {
    const items = Array.isArray(data.items) ? data.items : [];
    if (!append) listEl.innerHTML = "";
    listEl.innerHTML += items.map(rowHtml).join("");
    loadedCount += items.length;
    nextCursor = data.next_cursor || null;
    emptyEl.hidden = loadedCount > 0;
    pagerEl.hidden = !nextCursor;
    pagerMetaEl.textContent = `${loadedCount} loaded`;
  }

  async function load({ append }) {
    const params = new URLSearchParams({ limit: String(PAGE_LIMIT) });
    if (append && nextCursor) params.set("before", nextCursor);
    let response;
    try {
      response = await adminFetch(getToken(), `${endpoint}?${params}`);
    } catch {
      errorEl.textContent = "Couldn’t reach the server — try again.";
      errorEl.hidden = false;
      return null;
    }
    if (response.status === 401) {
      onUnauthorized();
      return null;
    }
    if (!response.ok) {
      errorEl.textContent = "Couldn’t load this list — try again.";
      errorEl.hidden = false;
      return null;
    }
    errorEl.hidden = true;
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
      const data = await load({ append: false });
      if (data !== null) render(data, { append: false });
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

  const loginView = document.getElementById("admin-login-view");
  const tableCard = document.getElementById("admin-table-card");
  const loginForm = document.getElementById("admin-login");
  const tokenInput = document.getElementById("admin-token");
  const toggleBtn = document.getElementById("admin-token-toggle");
  const loginSub = document.getElementById("admin-login-sub");
  const loginSubmit = document.getElementById("admin-login-submit");
  const footEl = document.getElementById("admin-login-foot");
  const logoutBtn = document.getElementById("admin-logout");
  const waitlistList = document.getElementById("admin-waitlist-list");

  const tabButtons = Array.from(document.querySelectorAll("[data-tab-btn]"));
  const tabPanels = {
    waitlist: document.getElementById("admin-tab-waitlist"),
    approved: document.getElementById("admin-tab-approved"),
  };

  const LOGIN_SUB = "Paste the admin bearer token to view and approve the waitlist.";
  const REJECTED_SUB = "That token was rejected. Check it and try again.";

  let token = readToken();
  let activeTab = "waitlist";
  const loadedTabs = new Set();

  function onUnauthorized() {
    showLogin(REJECTED_SUB);
  }

  const waitlistController = makeListController({
    endpoint: "/admin/invite/waitlist",
    rowHtml,
    listEl: waitlistList,
    emptyEl: document.getElementById("admin-empty"),
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
    listEl: document.getElementById("admin-approved-list"),
    emptyEl: document.getElementById("admin-approved-empty"),
    errorEl: document.getElementById("admin-approved-error"),
    pagerEl: document.getElementById("admin-approved-pager"),
    pagerMetaEl: document.getElementById("admin-approved-pager-meta"),
    loadMoreEl: document.getElementById("admin-approved-load-more"),
    getToken: () => token,
    onUnauthorized,
  });

  const controllers = { waitlist: waitlistController, approved: approvedController };

  function showLogin(message) {
    clearToken();
    token = "";
    tableCard.hidden = true;
    loginView.hidden = false;
    loginSub.textContent = message || LOGIN_SUB;
    loginSub.classList.toggle("invite-sub-error", Boolean(message));
    tokenInput.value = "";
    tokenInput.focus();
  }

  function setActiveTab(tab) {
    activeTab = tab;
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
      panel.hidden = name !== tab;
    }
    if (!loadedTabs.has(tab)) {
      loadedTabs.add(tab);
      controllers[tab].loadFirst();
    }
  }

  function showTable() {
    loginView.hidden = true;
    tableCard.hidden = false;
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
    footEl.hidden = true;
    token = candidate;
    const data = await waitlistController.loadFirst();
    setBusy(loginSubmit, false, "Sign in", "Signing in…");
    footEl.hidden = false;
    if (data === null) {
      token = "";
      return;
    }
    writeToken(token);
    loginView.hidden = true;
    tableCard.hidden = false;
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

  if (token) {
    showTable();
  }
}
