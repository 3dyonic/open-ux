export function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function setTitle(title) {
  document.title = title;
}

// Per uswds.dont-hide-then-reveal-alerts: inapplicable content should not sit
// in the DOM as visually hidden, waiting to be "revealed" — older AT can
// still perceive it. This moves `el` in or out of the DOM instead of
// toggling the `hidden` attribute. Capture `parent` once while `el` is still
// attached (e.g. right after ssr() renders it), since a detached el has no
// parentNode to fall back on.
export function setPresent(el, show, parent, anchor = null) {
  if (show) {
    if (el.parentNode !== parent || el.nextSibling !== anchor) {
      parent.insertBefore(el, anchor);
    }
  } else if (el.parentNode) {
    el.remove();
  }
}

export function ssr(page, inner, attrs = {}) {
  let extra = "";
  for (const [key, value] of Object.entries(attrs)) {
    if (value == null || value === "") continue;
    extra += ` data-ssr-${key}="${escapeHtml(String(value))}"`;
  }
  return `<div data-ssr-page="${escapeHtml(page)}"${extra}>${inner}</div>`;
}
