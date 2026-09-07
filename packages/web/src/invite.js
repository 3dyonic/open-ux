import { shell } from "./chrome.js";
import { escapeHtml, setTitle } from "./util.js";

const EMAIL_RE =
  /^[a-z0-9](?:[a-z0-9._+-]{0,62}[a-z0-9])?@(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/;
const TOKEN_RE = /^inv_[A-Za-z0-9_-]{16,64}$/;
const MASK = "uxmcp_" + "\u2022".repeat(16);

export function renderInvite(root) {
  setTitle("Open UX");
  root.innerHTML = shell(
    `
  <main class="main main--invite">
    <div class="card" id="request-card">
      <p class="meta"><span class="pip" aria-hidden="true"></span>Invite · waitlist, one key after approve</p>
      <p class="kicker" id="request-error-kicker"><span class="pip" aria-hidden="true"></span>REQUEST ERROR</p>
      <h1 class="title">Request access</h1>
      <p class="sub" id="request-sub">Join the waitlist. We email a one-time redeem when you are approved.</p>
      <form id="invite-request" method="post" action="/invite/request" novalidate>
        <div class="field">
          <label for="email">Email</label>
          <input class="field__input" id="email" name="email" type="email" autocomplete="email" inputmode="email" maxlength="254" spellcheck="false" autocapitalize="none" placeholder="you@studio.com" aria-describedby="email-error">
        </div>
        <p class="helper" id="email-error">Enter a valid email to request an invite.</p>
        <button class="btn btn--primary" type="submit">Request access</button>
        <a class="link" href="/invite/redeem">Already have a token? Redeem it.</a>
        <p class="foot" id="request-foot">No key yet — approval issues a one-time invite link.</p>
      </form>
    </div>
  </main>`,
    { catalog: false },
  );

  const DEFAULT_SUB = "Join the waitlist. We email a one-time redeem when you are approved.";
  const ERROR_SUB = "We couldn’t add you to the waitlist. Check the email and try again.";
  const form = document.getElementById("invite-request");
  const card = document.getElementById("request-card");
  const emailInput = document.getElementById("email");
  const helper = document.getElementById("email-error");
  const sub = document.getElementById("request-sub");
  const foot = document.getElementById("request-foot");

  function isValidEmail(value) {
    const email = value.trim().toLowerCase();
    return EMAIL_RE.test(email) && email.length <= 254;
  }

  function showError() {
    card.classList.add("card--error");
    emailInput.setAttribute("aria-invalid", "true");
    helper.classList.add("is-visible");
    sub.textContent = ERROR_SUB;
    foot.hidden = true;
  }

  function clearError() {
    card.classList.remove("card--error");
    emailInput.removeAttribute("aria-invalid");
    helper.classList.remove("is-visible");
    sub.textContent = DEFAULT_SUB;
    foot.hidden = false;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = emailInput.value.trim().toLowerCase();
    if (!isValidEmail(email)) {
      showError();
      return;
    }
    clearError();
    const res = await fetch("/invite/request", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email }),
    });
    await res.json();
    if (!res.ok) {
      showError();
      return;
    }
    window.location.href = "/invite/requested";
  });
}

export function renderRequested(root) {
  setTitle("Open UX");
  root.innerHTML = shell(
    `
  <main class="main main--invite">
    <div class="card" id="requested-card">
      <p class="meta"><span class="pip" aria-hidden="true"></span>Invite · waitlist</p>
      <h1 class="title">You’re on the list</h1>
      <p class="sub">Thanks — we’ll email a one-time invite when your request is approved.</p>
      <p class="foot">Already have an invite? Open the link from your email to redeem.</p>
      <p class="foot foot--meta">No key on this screen — key appears only after a real redeem.</p>
    </div>
  </main>`,
    { catalog: false },
  );
}

export function renderRedeem(root) {
  setTitle("Open UX");
  root.innerHTML = shell(
    `
  <main class="main main--invite">
    <div class="card" id="redeem-card">
      <p class="meta"><span class="pip" aria-hidden="true"></span>Invite · redeem once</p>
      <p class="kicker" id="redeem-error-kicker"><span class="pip" aria-hidden="true"></span>REDEEM ERROR</p>
      <h1 class="title">Redeem invite</h1>
      <p class="sub" id="redeem-sub">Paste your invite token, or open the link from your email.</p>
      <form id="invite-redeem" method="post" action="/invite/redeem" novalidate>
        <div class="field">
          <label for="token">Invite token</label>
          <input class="field__input" id="token" name="token" type="text" autocomplete="off" spellcheck="false" autocapitalize="none" maxlength="68" placeholder="inv_••••••••••••" aria-describedby="token-error">
        </div>
        <p class="helper" id="token-error">Invite invalid or already used. Request a new one if needed.</p>
        <button class="btn btn--primary" type="submit">Redeem</button>
        <p class="foot" id="redeem-foot">Redeeming burns the invite and mints your uxmcp_ key once.</p>
        <p class="foot foot--exclusive">Error is exclusive — Success / key is not shown on this state.</p>
      </form>
    </div>
    <div class="card" id="success-card" hidden>
      <p class="meta"><span class="pip" aria-hidden="true"></span>Redeemed · key once</p>
      <h1 class="title">Your key</h1>
      <p class="sub">Invite redeemed. Copy your key — we won’t show it in full again.</p>
      <div class="key" id="key-text"></div>
      <button class="btn btn--primary" type="button" id="copy-key">Copy</button>
      <p class="foot">Use as bearer on /mcp. Self-host stdio needs no auth.</p>
    </div>
  </main>`,
    { catalog: false },
  );

  const DEFAULT_SUB = "Paste your invite token, or open the link from your email.";
  const ERROR_SUB = "This invite isn’t valid. It may be used, expired, or mistyped.";
  let issuedKey = "";
  const form = document.getElementById("invite-redeem");
  const tokenInput = document.getElementById("token");
  const helper = document.getElementById("token-error");
  const sub = document.getElementById("redeem-sub");
  const foot = document.getElementById("redeem-foot");
  const redeemCard = document.getElementById("redeem-card");
  const successCard = document.getElementById("success-card");
  const keyText = document.getElementById("key-text");
  const params = new URLSearchParams(location.search);
  const q = params.get("token");
  if (q) tokenInput.value = q;

  function hideSuccess() {
    issuedKey = "";
    keyText.textContent = "";
    successCard.hidden = true;
  }

  function showError() {
    hideSuccess();
    redeemCard.hidden = false;
    redeemCard.classList.add("card--error");
    tokenInput.setAttribute("aria-invalid", "true");
    helper.classList.add("is-visible");
    sub.textContent = ERROR_SUB;
    foot.hidden = true;
  }

  function clearError() {
    redeemCard.classList.remove("card--error");
    tokenInput.removeAttribute("aria-invalid");
    helper.classList.remove("is-visible");
    sub.textContent = DEFAULT_SUB;
    foot.hidden = false;
  }

  function maskKey(key) {
    if (key.startsWith("uxmcp_")) return MASK;
    return "\u2022".repeat(16);
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const token = tokenInput.value.trim();
    if (!TOKEN_RE.test(token)) {
      showError();
      return;
    }
    clearError();
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
    redeemCard.hidden = true;
    successCard.hidden = false;
  });

  document.getElementById("copy-key").addEventListener("click", () => {
    if (!issuedKey || !navigator.clipboard) return;
    navigator.clipboard.writeText(issuedKey);
  });
}

export function renderNotFound(root, guidelineId) {
  setTitle("Not found — Open UX");
  root.innerHTML = shell(
    `
  <main class="main">
    <a class="back" href="/catalog">← Back to Catalog</a>
    <h1>Not found</h1>
    <p class="not-found">No guideline with id “${escapeHtml(guidelineId)}”.</p>
  </main>`,
    { catalogActive: true, paper: true },
  );
}
