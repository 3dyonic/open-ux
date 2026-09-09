export const CONSENT_COOKIE = "open_ux_gtm_consent";
export const CONSENT_GRANTED = "granted";
export const CONSENT_DENIED = "denied";
export const DEFAULT_GTM_ID = "GTM-N3BL3G9K";
export const CONSENT_BANNER_COPY =
  "We use cookies for analytics (Google Tag Manager / Google Analytics) to understand how the site is used.";

const GTM_ID_RE = /^GTM-[A-Z0-9]+$/;

let loading;

export function consentBannerHtml() {
  return `
  <aside class="consent" id="consent-banner" aria-label="Cookie banner">
    <p class="consent-copy">${CONSENT_BANNER_COPY} <a href="/privacy">Privacy</a></p>
    <div class="consent-actions">
      <button type="button" class="btn btn-primary min-h-11" id="consent-accept">Accept</button>
      <button type="button" class="btn btn-secondary min-h-11" id="consent-decline">Decline</button>
    </div>
  </aside>`;
}

export function analyticsAllowed(path = location.pathname) {
  const page = path.replace(/\/+$/, "") || "/";
  return page !== "/health" && page !== "/invite/redeem";
}

export function readFlag() {
  try {
    const stored = localStorage.getItem(CONSENT_COOKIE);
    if (stored === CONSENT_GRANTED || stored === CONSENT_DENIED) return stored;
  } catch {
    /* private mode */
  }
  const match = document.cookie.match(
    new RegExp(`(?:^|; )${CONSENT_COOKIE}=([^;]*)`),
  );
  const value = match ? decodeURIComponent(match[1]) : "";
  return value === CONSENT_GRANTED || value === CONSENT_DENIED ? value : "";
}

export function writeFlag(value) {
  document.cookie = `${CONSENT_COOKIE}=${value}; path=/; SameSite=Lax`;
  try {
    localStorage.setItem(CONSENT_COOKIE, value);
  } catch {
    /* private mode */
  }
}

async function resolveGtmId() {
  try {
    const response = await fetch("/api/site");
    if (response.ok) {
      const data = await response.json();
      const id = String(data.gtm_id || "").trim();
      if (GTM_ID_RE.test(id)) return id;
    }
  } catch {
    /* use default */
  }
  return DEFAULT_GTM_ID;
}

function injectGtm(id) {
  if (window.__openUxGtm || !GTM_ID_RE.test(id)) return;
  window.__openUxGtm = id;
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({ "gtm.start": Date.now(), event: "gtm.js" });
  const script = document.createElement("script");
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtm.js?id=${encodeURIComponent(id)}`;
  document.head.appendChild(script);
}

export function loadGtm() {
  if (!analyticsAllowed()) return Promise.resolve();
  if (window.__openUxGtm) return Promise.resolve();
  if (!loading) {
    loading = resolveGtmId().then((id) => {
      injectGtm(id);
    });
  }
  return loading;
}

function bindOnce() {
  if (bindOnce.done) return;
  bindOnce.done = true;
  document.addEventListener("click", (event) => {
    if (event.target.closest("#consent-accept")) {
      writeFlag(CONSENT_GRANTED);
      hideBanner();
      loadGtm();
      return;
    }
    if (event.target.closest("#consent-decline")) {
      const hadGtm = Boolean(window.__openUxGtm);
      writeFlag(CONSENT_DENIED);
      hideBanner();
      if (hadGtm) location.reload();
      return;
    }
    if (event.target.closest("#cookie-settings")) {
      const banner = document.getElementById("consent-banner");
      if (banner) banner.hidden = false;
    }
  });
}

function hideBanner() {
  const banner = document.getElementById("consent-banner");
  if (banner) banner.hidden = true;
}

export function mountConsent() {
  const flag = readFlag();
  const banner = document.getElementById("consent-banner");
  if (banner) {
    banner.hidden = flag === CONSENT_GRANTED || flag === CONSENT_DENIED;
  }
  if (flag === CONSENT_GRANTED) loadGtm();
  bindOnce();
}
