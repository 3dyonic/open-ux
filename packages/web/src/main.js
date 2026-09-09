import { renderCatalog, renderRule } from "./catalog.js";
import { renderHealth } from "./health.js";
import { renderNotFound, renderServerError } from "./errors.js";
import { renderInvite, renderRedeem, renderRequested } from "./invite.js";
import { renderLanding } from "./landing.js";
import { renderPrivacy } from "./privacy.js";
import { renderSources } from "./sources.js";
import "./styles.css";

function route() {
  const root = document.getElementById("app");
  const ssrPage = root.querySelector("[data-ssr-page]");
  const painted = ssrPage?.getAttribute("data-ssr-page") || "";
  if (painted === "landing") return renderLanding(root);
  if (painted === "not-found" || painted === "server-error") return;
  if (painted === "privacy") return renderPrivacy(root);
  if (painted === "sources") return renderSources(root);
  if (painted === "requested") return renderRequested(root);
  const path = location.pathname.replace(/\/+$/, "") || "/";
  if (path === "/") return renderLanding(root);
  if (path === "/catalog") return renderCatalog(root);
  const rule = path.match(/^\/catalog\/(.+)$/);
  if (rule) return renderRule(root, decodeURIComponent(rule[1]));
  if (path === "/health") return renderHealth(root);
  if (path === "/privacy") return renderPrivacy(root);
  if (path === "/sources") return renderSources(root);
  if (path === "/invite") return renderInvite(root);
  if (path === "/invite/requested") return renderRequested(root);
  if (path === "/invite/redeem") return renderRedeem(root);
  return renderNotFound(root, path);
}

function catalogPath(url) {
  const path = url.pathname.replace(/\/+$/, "") || "/";
  return path === "/catalog" || path.startsWith("/catalog/");
}

document.addEventListener("click", (event) => {
  if (event.defaultPrevented || event.button !== 0) return;
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  const link = event.target.closest("a[href]");
  if (!link || link.target === "_blank" || link.hasAttribute("download")) return;
  let url;
  try {
    url = new URL(link.href, location.origin);
  } catch {
    return;
  }
  if (url.origin !== location.origin || !catalogPath(url)) return;
  event.preventDefault();
  const next = url.pathname + url.search;
  const here = location.pathname + location.search;
  if (next !== here) history.pushState(null, "", next);
  route();
});

window.addEventListener("popstate", () => {
  route();
});

route();
