import { renderCatalog, renderRule } from "./catalog.js";
import { renderHealth } from "./health.js";
import { renderInvite, renderNotFound, renderRedeem, renderRequested } from "./invite.js";
import { renderLanding } from "./landing.js";
import { renderPrivacy } from "./privacy.js";
import { renderSources } from "./sources.js";
import "./styles.css";

function route() {
  const root = document.getElementById("app");
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

route();
