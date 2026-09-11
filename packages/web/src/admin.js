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
  <main class="page page-invite">
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

    <div class="page w-full max-w-[760px]" id="admin-table-card" hidden>
      <div class="flex items-center justify-between gap-4">
        <div class="flex flex-col gap-1">
          <p class="invite-meta"><span class="pip" aria-hidden="true"></span>Admin · invite waitlist</p>
          <h1 class="page-title">Invite waitlist</h1>
        </div>
        <button class="btn btn-outline btn-nav" type="button" id="admin-logout">Sign out</button>
      </div>
      <p class="invite-sub invite-sub-error" id="admin-table-error" hidden></p>
      <div class="list" id="admin-waitlist-list"></div>
      <p class="lede" id="admin-empty" hidden>No one on the waitlist yet.</p>
      <div class="pager" id="admin-pager" hidden>
        <a class="back" href="#admin-table-card" id="admin-back-to-top">↑ Back to top</a>
        <p class="pager-meta" id="admin-pager-meta"></p>
        <button class="btn btn-outline" type="button" id="admin-load-more">Load more</button>
      </div>
    </div>
  </main>`,
        { catalog: false, key: false, consent: false, paper: true },
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

export function renderAdmin(root) {
  const page = adminPage();
  setTitle(page.title);
  if (!root.querySelector('[data-ssr-page="admin"]')) {
    root.innerHTML = page.body;
  }

  const loginCard = document.getElementById("admin-login-card");
  const tableCard = document.getElementById("admin-table-card");
  const loginForm = document.getElementById("admin-login");
  const tokenInput = document.getElementById("admin-token");
  const toggleBtn = document.getElementById("admin-token-toggle");
  const loginSub = document.getElementById("admin-login-sub");
  const loginSubmit = document.getElementById("admin-login-submit");
  const footEl = document.getElementById("admin-login-foot");
  const logoutBtn = document.getElementById("admin-logout");
  const list = document.getElementById("admin-waitlist-list");
  const emptyEl = document.getElementById("admin-empty");
  const tableError = document.getElementById("admin-table-error");
  const pager = document.getElementById("admin-pager");
  const pagerMeta = document.getElementById("admin-pager-meta");
  const loadMoreBtn = document.getElementById("admin-load-more");

  const LOGIN_SUB = "Paste the admin bearer token to view and approve the waitlist.";
  const REJECTED_SUB = "That token was rejected. Check it and try again.";

  let token = readToken();
  let nextCursor = null;
  let loadedCount = 0;

  function showLogin(message) {
    clearToken();
    token = "";
    tableCard.hidden = true;
    loginCard.hidden = false;
    loginSub.textContent = message || LOGIN_SUB;
    loginSub.classList.toggle("invite-sub-error", Boolean(message));
    tokenInput.value = "";
    tokenInput.focus();
  }

  function showTable() {
    loginCard.hidden = true;
    tableCard.hidden = false;
    list.innerHTML = "";
    tableError.hidden = true;
    loadedCount = 0;
    nextCursor = null;
  }

  function onUnauthorized() {
    showLogin(REJECTED_SUB);
  }

  function renderPage(data, { append } = { append: false }) {
    const items = Array.isArray(data.items) ? data.items : [];
    if (!append) list.innerHTML = "";
    list.innerHTML += items.map(rowHtml).join("");
    loadedCount += items.length;
    nextCursor = data.next_cursor || null;
    emptyEl.hidden = loadedCount > 0;
    pager.hidden = !nextCursor;
    pagerMeta.textContent = `${loadedCount} loaded`;
    loadMoreBtn.disabled = false;
  }

  async function loadPage({ append } = { append: false }) {
    const params = new URLSearchParams({ limit: String(PAGE_LIMIT) });
    if (append && nextCursor) params.set("before", nextCursor);
    let response;
    try {
      response = await adminFetch(token, `/admin/invite/waitlist?${params}`);
    } catch {
      tableError.textContent = "Couldn’t reach the server — try again.";
      tableError.hidden = false;
      return null;
    }
    if (response.status === 401) {
      onUnauthorized();
      return null;
    }
    if (!response.ok) {
      tableError.textContent = "Couldn’t load the waitlist — try again.";
      tableError.hidden = false;
      return null;
    }
    tableError.hidden = true;
    return response.json();
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
    const data = await loadPage({ append: false });
    setBusy(loginSubmit, false, "Sign in", "Signing in…");
    footEl.hidden = false;
    if (data === null) return;
    writeToken(token);
    showTable();
    renderPage(data, { append: false });
  });

  logoutBtn.addEventListener("click", () => {
    showLogin();
  });

  loadMoreBtn.addEventListener("click", async () => {
    setBusy(loadMoreBtn, true, "Load more", "Loading…");
    const data = await loadPage({ append: true });
    if (data !== null) renderPage(data, { append: true });
    setBusy(loadMoreBtn, false, "Load more", "Loading…");
  });

  list.addEventListener("click", (event) => {
    const button = event.target.closest("[data-approve]");
    if (!button) return;
    const row = button.closest(".admin-row");
    if (!row) return;
    approveRow(token, row, onUnauthorized);
  });

  if (token) {
    showTable();
    loadPage({ append: false }).then((data) => {
      if (data !== null) renderPage(data, { append: false });
    });
  }
}
