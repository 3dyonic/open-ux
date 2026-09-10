import { shell } from "./chrome.js";
import { escapeHtml, setTitle, ssr } from "./util.js";

const EMAIL_RE =
  /^[a-z0-9](?:[a-z0-9._+-]{0,62}[a-z0-9])?@(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/;
const TOKEN_RE = /^inv_[A-Za-z0-9_-]{16,64}$/;
const MASK = "uxmcp_" + "\u2022".repeat(16);

const CARD = "invite-card";
const CARD_ERROR = "invite-card invite-card-error";

function setBusy(button, busy, idleLabel, busyLabel) {
  button.disabled = busy;
  button.setAttribute("aria-busy", busy ? "true" : "false");
  button.classList.toggle("btn-busy", busy);
  button.textContent = busy ? busyLabel : idleLabel;
}

function setFieldError(card, input, sub, error) {
  card.className = CARD_ERROR;
  input.setAttribute("aria-invalid", "true");
  input.setAttribute("aria-describedby", sub.id);
  sub.className = "invite-sub invite-sub-error";
  sub.textContent = error;
  input.focus();
}

function clearFieldError(card, input, sub, supporting) {
  card.className = CARD;
  input.removeAttribute("aria-invalid");
  input.removeAttribute("aria-describedby");
  sub.className = "invite-sub";
  sub.textContent = supporting;
}

const INVITE_TITLE = "Request access — Open UX";
const INVITE_DESCRIPTION =
  "Join the waitlist. We email a one-time redeem when you are approved.";

export function invitePage() {
  return {
    title: INVITE_TITLE,
    description: INVITE_DESCRIPTION,
    path: "/invite",
    body: ssr(
      "invite",
      shell(
        `
  <main class="page page-invite">
    <div class="${CARD}" id="request-card">
      <p class="invite-meta"><span class="pip" aria-hidden="true"></span>Invite · waitlist, one key after approve</p>
      <h1 class="invite-title">Request access</h1>
      <p class="invite-sub" id="request-sub">${INVITE_DESCRIPTION}</p>
      <form id="invite-request" class="contents" method="post" action="/invite/request" novalidate>
        <div class="field-invite">
          <label class="label-invite" for="email">Email</label>
          <input class="input input-invite" id="email" name="email" type="email" autocomplete="email" inputmode="email" maxlength="254" spellcheck="false" autocapitalize="none" placeholder="you@studio.com">
        </div>
        <button class="btn btn-primary" type="submit" id="request-submit">Request access</button>
        <a class="invite-link" href="/invite/redeem">Already have a token? Redeem it.</a>
        <p class="foot" id="request-foot">No key yet — approval issues a one-time invite link.</p>
      </form>
    </div>
  </main>`,
        { catalog: false },
      ),
    ),
  };
}

export function requestedPage() {
  return {
    title: "You’re on the list — Open UX",
    description: "Thanks — we’ll email a one-time invite when your request is approved.",
    path: "/invite/requested",
    index: false,
    body: ssr(
      "requested",
      shell(
        `
  <main class="page page-invite">
    <div class="${CARD}" id="requested-card">
      <p class="invite-meta"><span class="pip" aria-hidden="true"></span>Invite · waitlist</p>
      <h1 class="invite-title">You’re on the list</h1>
      <p class="invite-sub">Thanks — we’ll email a one-time invite when your request is approved.</p>
      <p class="foot">Already have an invite? Open the link from your email to redeem.</p>
      <p class="foot foot-meta">No key on this screen — key appears only after a real redeem.</p>
    </div>
  </main>`,
        { catalog: false },
      ),
    ),
  };
}

export function redeemPage() {
  return {
    title: "Redeem invite — Open UX",
    description: "Paste your invite token, or open the link from your email.",
    path: "/invite/redeem",
    index: false,
    body: ssr(
      "redeem",
      shell(
        `
  <main class="page page-invite">
    <div class="${CARD}" id="redeem-card">
      <p class="invite-meta"><span class="pip" aria-hidden="true"></span>Invite · redeem once</p>
      <h1 class="invite-title">Redeem invite</h1>
      <p class="invite-sub" id="redeem-sub">Paste your invite token, or open the link from your email.</p>
      <form id="invite-redeem" class="contents" method="post" action="/invite/redeem" novalidate>
        <div class="field-invite">
          <label class="label-invite" for="token">Invite token</label>
          <input class="input input-invite" id="token" name="token" type="text" autocomplete="off" spellcheck="false" autocapitalize="none" maxlength="68" placeholder="inv_••••••••••••">
        </div>
        <button class="btn btn-primary" type="submit" id="redeem-submit">Redeem</button>
        <p class="foot" id="redeem-foot">Redeeming burns the invite and mints your uxmcp_ key once.</p>
      </form>
    </div>
    <div class="${CARD}" id="success-card" hidden>
      <p class="invite-meta"><span class="pip" aria-hidden="true"></span>Redeemed · key once</p>
      <h1 class="invite-title">Your key</h1>
      <p class="invite-sub">Invite redeemed. Copy your key — we won’t show it in full again.</p>
      <div class="key-box" id="key-text"></div>
      <button class="btn btn-primary" type="button" id="copy-key">Copy key</button>
      <p class="invite-sub">Add this MCP server in your client — paste into <span class="font-mono text-ink">mcp.json</span> or your editor’s MCP settings.</p>
      <pre class="config-box" id="mcp-config"></pre>
      <button class="btn btn-outline" type="button" id="copy-mcp-config">Copy MCP config</button>
      <p class="foot">Bearer key only. Plugins from GitHub add skill and slash commands; MCP config alone enables the tools.</p>
    </div>
  </main>`,
        { catalog: false, consent: false },
      ),
    ),
  };
}

export function renderInvite(root) {
  const page = invitePage();
  setTitle(page.title);
  const supporting = INVITE_DESCRIPTION;
  if (!root.querySelector('[data-ssr-page="invite"]')) {
    root.innerHTML = page.body;
  }
  const invalidEmail = "Enter a valid email to request an invite";
  const requestFailed = "We couldn’t add you to the waitlist. Check the email and try again.";

  const form = document.getElementById("invite-request");
  const card = document.getElementById("request-card");
  const emailInput = document.getElementById("email");
  const sub = document.getElementById("request-sub");
  const submit = document.getElementById("request-submit");
  const footEl = document.getElementById("request-foot");

  function isValidEmail(value) {
    const email = value.trim().toLowerCase();
    return EMAIL_RE.test(email) && email.length <= 254;
  }

  function showError(message) {
    setBusy(submit, false, "Request access", "Requesting…");
    setFieldError(card, emailInput, sub, message);
    footEl.hidden = true;
  }

  function clearError() {
    clearFieldError(card, emailInput, sub, supporting);
    footEl.hidden = false;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = emailInput.value.trim().toLowerCase();
    if (!isValidEmail(email)) {
      showError(invalidEmail);
      return;
    }
    clearError();
    setBusy(submit, true, "Request access", "Requesting…");
    try {
      const res = await fetch("/invite/request", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email }),
      });
      await res.json();
      if (!res.ok) {
        showError(requestFailed);
        return;
      }
      window.location.href = "/invite/requested";
    } catch {
      showError(requestFailed);
    }
  });
}

export function renderRequested(root) {
  const page = requestedPage();
  setTitle(page.title);
  if (root.querySelector('[data-ssr-page="requested"]')) return;
  root.innerHTML = page.body;
}

export function renderRedeem(root) {
  const page = redeemPage();
  setTitle(page.title);
  const supporting = page.description;
  const invalidToken = "This invite isn’t valid. It may be used, expired, or mistyped.";
  if (!root.querySelector('[data-ssr-page="redeem"]')) {
    root.innerHTML = page.body;
  }

  let issuedKey = "";
  const form = document.getElementById("invite-redeem");
  const tokenInput = document.getElementById("token");
  const sub = document.getElementById("redeem-sub");
  const submit = document.getElementById("redeem-submit");
  const footEl = document.getElementById("redeem-foot");
  const redeemCard = document.getElementById("redeem-card");
  const successCard = document.getElementById("success-card");
  const keyText = document.getElementById("key-text");
  const mcpConfig = document.getElementById("mcp-config");
  const params = new URLSearchParams(location.search);
  const q = params.get("token");
  if (q) tokenInput.value = q;

  function hideSuccess() {
    issuedKey = "";
    keyText.textContent = "";
    mcpConfig.textContent = "";
    successCard.hidden = true;
    setTitle("Redeem invite — Open UX");
  }

  function showError() {
    hideSuccess();
    redeemCard.hidden = false;
    setBusy(submit, false, "Redeem", "Redeeming…");
    setFieldError(redeemCard, tokenInput, sub, invalidToken);
    footEl.hidden = true;
  }

  function clearError() {
    clearFieldError(redeemCard, tokenInput, sub, supporting);
    footEl.hidden = false;
  }

  function maskKey(key) {
    if (key.startsWith("uxmcp_")) return MASK;
    return "\u2022".repeat(16);
  }

  function mcpConfigText(key) {
    const mcpUrl = `${location.origin}/mcp`;
    return JSON.stringify(
      {
        mcpServers: {
          "open-ux": {
            url: mcpUrl,
            headers: {
              Authorization: `Bearer ${key}`,
            },
          },
        },
      },
      null,
      2,
    );
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const token = tokenInput.value.trim();
    if (!TOKEN_RE.test(token)) {
      showError();
      return;
    }
    clearError();
    setBusy(submit, true, "Redeem", "Redeeming…");
    try {
      const res = await fetch("/invite/redeem", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ token }),
      });
      const data = await res.json();
      if (!res.ok || !data.key) {
        showError();
        return;
      }
      issuedKey = data.key;
      keyText.textContent = maskKey(issuedKey);
      mcpConfig.textContent = mcpConfigText(issuedKey);
      redeemCard.hidden = true;
      successCard.hidden = false;
      setTitle("Your key — Open UX");
    } catch {
      showError();
    }
  });

  document.getElementById("copy-key").addEventListener("click", () => {
    if (!issuedKey || !navigator.clipboard) return;
    navigator.clipboard.writeText(issuedKey);
  });

  document.getElementById("copy-mcp-config").addEventListener("click", () => {
    if (!issuedKey || !navigator.clipboard) return;
    navigator.clipboard.writeText(mcpConfigText(issuedKey));
  });
}

