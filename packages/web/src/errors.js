import { shell } from "./chrome.js";
import { escapeHtml, setTitle, ssr } from "./util.js";

const PIP_HOLD = `<svg class="error-pip" xmlns="http://www.w3.org/2000/svg" width="280" height="220" viewBox="0 0 280 220" aria-hidden="true"><ellipse cx="123" cy="199" rx="75" ry="11" fill="#D6BEA6" fill-opacity="0.55"/><ellipse cx="62" cy="127" rx="20" ry="9" transform="rotate(22 62 127)" fill="#ECDCCA"/><circle cx="123" cy="107" r="59" fill="#FF4B00"/><ellipse cx="109" cy="81" rx="23" ry="11" fill="#FFC79E" fill-opacity="0.7"/><ellipse cx="104" cy="103" rx="4" ry="5" fill="#1F1B16"/><ellipse cx="134" cy="103" rx="4" ry="5" fill="#1F1B16"/><ellipse cx="121" cy="123" rx="8" ry="2.5" fill="#B8330D"/><ellipse cx="189" cy="117" rx="21" ry="9" transform="rotate(-22 189 117)" fill="#ECDCCA"/><rect x="168" y="58" width="54" height="68" rx="6" fill="#FFFFFF" stroke="#DED4C8"/></svg>`;

const PIP_LOOK = `<svg class="error-pip" xmlns="http://www.w3.org/2000/svg" width="280" height="220" viewBox="0 0 280 220" aria-hidden="true"><ellipse cx="140" cy="199" rx="75" ry="11" fill="#D6BEA6" fill-opacity="0.55"/><rect x="178" y="142" width="54" height="68" rx="6" fill="#FFFFFF" stroke="#DED4C8" transform="rotate(-22 205 176)"/><ellipse cx="72" cy="139" rx="18" ry="9" transform="rotate(10 72 139)" fill="#ECDCCA"/><circle cx="140" cy="101" r="59" fill="#FF4B00"/><ellipse cx="126" cy="75" rx="23" ry="11" fill="#FFC79E" fill-opacity="0.7"/><ellipse cx="122" cy="109" rx="4" ry="5" fill="#1F1B16"/><ellipse cx="152" cy="113" rx="4" ry="5" fill="#1F1B16"/><ellipse cx="140" cy="126" rx="6" ry="2" fill="#B8330D"/><ellipse cx="196" cy="133" rx="18" ry="9" transform="rotate(-8 196 133)" fill="#ECDCCA"/></svg>`;

export function notFoundPage(detail = "", { kind = "page" } = {}) {
  const label = String(detail || "").trim();
  const isRule = kind === "rule";
  const kicker = isRule ? "Missing rule" : "Not found";
  const lede = isRule
    ? "This id is not in the catalog. Open the catalog to pick another."
    : "This page is not here. Open the catalog to pick a rule.";
  const chip = isRule ? label || "unknown.id" : label;
  return {
    title: "Not found — Open UX",
    description: lede,
    path: "/404",
    index: false,
    body: ssr(
      "not-found",
      shell(
        `
  <main class="page page-error">
    ${PIP_HOLD}
    <div class="error-copy">
      <p class="kicker"><span class="pip" aria-hidden="true"></span>${escapeHtml(kicker)}</p>
      <h1 class="page-title">Not found</h1>
      <p class="lede">${escapeHtml(lede)}</p>
      ${chip ? `<p class="error-id">${escapeHtml(chip)}</p>` : ""}
      <a class="btn btn-primary" href="/catalog">Browse catalog</a>
    </div>
  </main>`,
        { catalogActive: isRule, paper: true },
      ),
      { kind, detail: label },
    ),
  };
}

export function serverErrorPage(path = "/") {
  const href = path || "/";
  return {
    title: "This page could not be loaded — Open UX",
    description: "Try again in a moment.",
    path: "/500",
    index: false,
    body: ssr(
      "server-error",
      shell(
        `
  <main class="page page-error">
    ${PIP_LOOK}
    <div class="error-copy">
      <p class="kicker"><span class="pip" aria-hidden="true"></span>Error</p>
      <h1 class="page-title error-title">This page could not be loaded</h1>
      <p class="lede">Try again in a moment.</p>
      <a class="btn btn-primary" href="${escapeHtml(href)}">Try again</a>
    </div>
  </main>`,
        { paper: true },
      ),
    ),
  };
}

export function renderNotFound(root, detail = "", options = {}) {
  const page = notFoundPage(detail, options);
  setTitle(page.title);
  root.innerHTML = page.body;
}

export function renderServerError(root, path = "/") {
  const page = serverErrorPage(path || "/");
  setTitle(page.title);
  root.innerHTML = page.body;
}
