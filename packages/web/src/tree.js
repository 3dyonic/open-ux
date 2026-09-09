import { escapeHtml } from "./util.js";
import { displayName, hrefId, locate } from "./catalog-model.js";

function facetKey(containerId, cardId, facetId) {
  return `${containerId}\0${cardId}\0${facetId}`;
}

function indexByFacet(index, jobs) {
  const byFacet = new Map();
  for (const row of index || []) {
    const here = locate(row, jobs);
    if (!here.container || !here.card || !here.facet) continue;
    const key = facetKey(here.container, here.card, here.facet);
    if (!byFacet.has(key)) byFacet.set(key, []);
    byFacet.get(key).push(row);
  }
  return byFacet;
}

const CARET = `<svg class="tree-caret-icon" viewBox="0 0 16 16" width="16" height="16" fill="none" aria-hidden="true"><path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

function lead(kind) {
  if (kind === "rule") {
    return `<span class="tree-caret tree-caret-leaf" aria-hidden="true"></span>`;
  }
  return `<span class="tree-caret" aria-hidden="true">${CARET}</span>`;
}

function groupOpen(kind, id, title, { open = false, here = false }) {
  const group = ["tree-group"];
  if (open) group.push("is-open");
  const item = ["tree-item", `tree-${kind}`];
  if (here) item.push("is-here");
  return `<div class="${group.join(" ")}" data-tree="${escapeHtml(kind)}" data-id="${escapeHtml(id)}"><button type="button" class="${item.join(" ")}" aria-expanded="${open ? "true" : "false"}">${lead(kind)}<span class="tree-label">${escapeHtml(title)}</span></button><div class="tree-children">`;
}

function ruleItem(row, currentId) {
  const gid = String(row.id || "");
  const current = gid === currentId;
  const cls = ["tree-item", "tree-rule"];
  if (current) cls.push("is-current");
  const aria = current ? ' aria-current="page"' : "";
  return `<a class="${cls.join(" ")}" href="${escapeHtml(hrefId(gid))}" data-tree="rule" data-tree-rule data-id="${escapeHtml(gid)}"${aria}>${lead("rule")}<span class="tree-label">${escapeHtml(displayName(row))}</span></a>`;
}

function setOpen(group, open) {
  if (!group) return;
  if (open) {
    const parent = group.parentElement;
    for (const sibling of parent ? parent.children : []) {
      if (sibling === group || !sibling.classList?.contains("tree-group")) continue;
      sibling.classList.remove("is-open");
      const other = sibling.querySelector(":scope > .tree-item[aria-expanded]");
      if (other) other.setAttribute("aria-expanded", "false");
    }
  }
  group.classList.toggle("is-open", open);
  const btn = group.querySelector(":scope > .tree-item[aria-expanded]");
  if (btn) btn.setAttribute("aria-expanded", open ? "true" : "false");
}

export function treeHtml(jobs, index, current) {
  const containers = jobs?.containers || [];
  const cards = jobs?.cards || [];
  if (!containers.length) return "";
  const here = locate(current, jobs, index);
  const byFacet = indexByFacet(index, jobs);
  const parts = [`<nav class="sidebar" id="catalog-tree" aria-label="Catalog tree">`];

  for (const container of containers) {
    const cardRows = cards.filter((card) => card.container === container.id);
    const liveCards = [];
    for (const card of cardRows) {
      const liveFacets = [];
      for (const facet of card.facets || []) {
        const rows = byFacet.get(facetKey(container.id, card.id, facet.id)) || [];
        if (!rows.length) continue;
        liveFacets.push({ facet, rows });
      }
      if (!liveFacets.length) continue;
      liveCards.push({ card, liveFacets });
    }
    if (!liveCards.length) continue;

    const openC = container.id === here.container;
    parts.push(
      groupOpen("container", container.id, container.title, { open: openC, here: openC }),
    );
    for (const { card, liveFacets } of liveCards) {
      const openCard = openC && card.id === here.card;
      const hereCard = card.id === here.card;
      parts.push(
        groupOpen("card", card.id, card.title, { open: openCard, here: hereCard }),
      );
      for (const { facet, rows } of liveFacets) {
        const openF = openCard && facet.id === here.facet;
        const hereFacet = hereCard && facet.id === here.facet;
        parts.push(
          groupOpen("facet", facet.id, facet.title, { open: openF, here: hereFacet }),
        );
        for (const row of rows) {
          const gid = String(row.id || "");
          if (!gid) continue;
          parts.push(ruleItem(row, here.id));
        }
        parts.push("</div></div>");
      }
      parts.push("</div></div>");
    }
    parts.push("</div></div>");
  }

  parts.push("</nav>");
  return parts.join("");
}

export function bindTree() {
  const tree = document.getElementById("catalog-tree");
  if (!tree || tree.dataset.bound === "1") return;
  tree.dataset.bound = "1";
  tree.addEventListener("click", (event) => {
    const btn = event.target.closest("button.tree-item[aria-expanded]");
    if (!btn || !tree.contains(btn)) return;
    const group = btn.parentElement;
    if (!group || !group.classList.contains("tree-group")) return;
    setOpen(group, btn.getAttribute("aria-expanded") !== "true");
  });
}

export function syncTree(tree, guidelineId) {
  if (!tree) return;
  const want = String(guidelineId || "");
  const link = [...tree.querySelectorAll("[data-tree-rule]")].find(
    (el) => el.getAttribute("data-id") === want,
  );
  if (!link) return;

  for (const el of tree.querySelectorAll(".is-here, .is-current")) {
    el.classList.remove("is-here", "is-current");
  }
  for (const el of tree.querySelectorAll("[aria-current]")) {
    el.removeAttribute("aria-current");
  }

  link.classList.add("is-current");
  link.setAttribute("aria-current", "page");

  const facetGroup = link.closest('[data-tree="facet"]');
  const cardGroup = facetGroup?.closest('[data-tree="card"]') || link.closest('[data-tree="card"]');
  const containerGroup =
    cardGroup?.closest('[data-tree="container"]') || link.closest('[data-tree="container"]');
  const facetBtn = facetGroup?.querySelector(":scope > .tree-item");
  const cardBtn = cardGroup?.querySelector(":scope > .tree-item");
  const containerBtn = containerGroup?.querySelector(":scope > .tree-item");
  if (facetBtn) facetBtn.classList.add("is-here");
  if (cardBtn) cardBtn.classList.add("is-here");
  if (containerBtn) containerBtn.classList.add("is-here");

  const keep = new Set([facetGroup, cardGroup, containerGroup].filter(Boolean));
  for (const group of tree.querySelectorAll(".tree-group.is-open")) {
    if (!keep.has(group)) setOpen(group, false);
  }
  setOpen(facetGroup, true);
  setOpen(cardGroup, true);
  setOpen(containerGroup, true);
}
