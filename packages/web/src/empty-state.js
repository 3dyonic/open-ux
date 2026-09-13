import { PIP_LOOK } from "./errors.js";
import { escapeHtml } from "./util.js";

export function emptyStateHtml(message) {
  return `
  <div class="empty-state">
    ${PIP_LOOK}
    <p class="lede">${escapeHtml(message)}</p>
  </div>`;
}
