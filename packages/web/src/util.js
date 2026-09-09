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

export function ssr(page, inner, attrs = {}) {
  let extra = "";
  for (const [key, value] of Object.entries(attrs)) {
    if (value == null || value === "") continue;
    extra += ` data-ssr-${key}="${escapeHtml(String(value))}"`;
  }
  return `<div data-ssr-page="${escapeHtml(page)}"${extra}>${inner}</div>`;
}
