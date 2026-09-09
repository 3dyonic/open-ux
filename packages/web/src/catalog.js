import { shell } from "./chrome.js";
import { renderNotFound, renderServerError } from "./errors.js";
import { escapeHtml, setTitle, ssr } from "./util.js";

const SOURCE_HOUSES = {
  ant: "Ant",
  nng: "NN/g",
  govuk: "GOV.UK",
  fluent: "Fluent",
  polar: "Polaris",
  spectrum: "Spectrum",
  uswds: "USWDS",
  canada: "Canada.ca",
  nsw: "NSW",
  gold: "GOLD",
  nl: "NL",
  suomi: "Suomi.fi",
  mui: "MUI",
  apple: "Apple",
  vercel: "Vercel",
  material: "Material",
  tidwell: "Tidwell",
};

const SOURCE_SUFFIXES = Object.values(SOURCE_HOUSES)
  .sort((a, b) => b.length - a.length)
  .map((label) => ` — ${label}`);

export const CONTAINER_CHIPS = [
  ["forms_and_input", "Forms"],
  ["actions_and_decisions", "Actions"],
  ["feedback_and_status", "Feedback"],
  ["navigation_and_wayfinding", "Wayfinding"],
  ["layout_and_data_display", "Layout"],
  ["overlays_and_content_structure", "Overlays"],
  ["multi_step_flows", "Multi-step"],
];

const CHIP_IDS = new Set(CONTAINER_CHIPS.map(([id]) => id));
export const PAGE_SIZE = 25;

let indexCache = null;
let indexPending = null;
let ruleGen = 0;

function loadIndex() {
  if (indexCache) return Promise.resolve(indexCache);
  if (!indexPending) {
    indexPending = fetch("/api/catalog")
      .then((res) => {
        if (!res.ok) throw new Error("catalog");
        return res.json();
      })
      .then((data) => {
        indexCache = data;
        return data;
      })
      .finally(() => {
        indexPending = null;
      });
  }
  return indexPending;
}

function stripHouseSuffix(name) {
  let text = String(name || "").trim();
  for (const suffix of SOURCE_SUFFIXES) {
    if (text.endsWith(suffix)) return text.slice(0, -suffix.length).trimEnd();
  }
  return text;
}

function rawName(row) {
  return String(row.name || row.title || row.id || "");
}

export function displayName(row) {
  return stripHouseSuffix(rawName(row));
}

export function displayId(guidelineId) {
  const text = String(guidelineId || "").trim();
  if (!text.includes(".")) return text;
  const [lane, rest] = text.split(".", 2);
  if (rest && lane in SOURCE_HOUSES) return rest;
  return text;
}

function searchBlob(row) {
  const gid = String(row.id || "");
  return `${displayId(gid)} ${row.title || ""} ${displayName(row)}`.toLowerCase();
}

function hrefId(guidelineId) {
  return "/catalog/" + encodeURIComponent(guidelineId).replace(/%2E/g, ".");
}

function cardById(jobs, cardId) {
  return (jobs.cards || []).find((card) => card.id === cardId) || null;
}

function containerTitle(jobs, containerId) {
  if (!containerId) return "";
  const found = (jobs.containers || []).find((item) => item.id === containerId);
  return found ? found.title : containerId;
}

function cardTitle(jobs, cardId) {
  if (!cardId) return "";
  const card = cardById(jobs, cardId);
  return card ? card.title : cardId;
}

function rowContainer(row, jobs) {
  const raw = String(row.container || "").trim();
  if (raw) return raw;
  const card = cardById(jobs, String(row.card || ""));
  if (card && card.container) return String(card.container);
  const facetId = String(row.facet || "");
  if (facetId) {
    for (const item of jobs.cards || []) {
      if ((item.facets || []).some((facet) => facet.id === facetId)) {
        return String(item.container);
      }
    }
  }
  return "";
}

function rowPath(row, jobs) {
  const left = containerTitle(jobs, rowContainer(row, jobs) || row.container);
  const right = cardTitle(jobs, row.card);
  if (left && right) return `${left} / ${right}`;
  return left || right;
}

function pagerMeta(total, page, size = PAGE_SIZE) {
  if (total <= 0) return "0 of 0";
  const pages = Math.max(1, Math.ceil(total / size));
  page = Math.min(Math.max(page, 1), pages);
  const start = (page - 1) * size + 1;
  const end = Math.min(page * size, total);
  return `${start}–${end} of ${total}`;
}

function chipsHtml(selected) {
  const wanted = CHIP_IDS.has(selected) ? selected : "";
  const items = [["", "All"], ...CONTAINER_CHIPS]
    .map(([id, label]) => {
      const on = id === wanted;
      return `<button type="button" class="${on ? "chip chip-on" : "chip"}" data-chip="${escapeHtml(id)}" aria-pressed="${on ? "true" : "false"}">${escapeHtml(label)}</button>`;
    })
    .join("");
  return `<div class="chips" id="catalog-chips">${items}</div>`;
}

function rowHtml(row, jobs, hidden) {
  const gid = String(row.id || "");
  const name = displayName(row);
  const path = rowPath(row, jobs);
  const cid = rowContainer(row, jobs);
  const rule = String(row.rule || "").trim();
  let line = `<span class="row-name">${escapeHtml(name)}</span>`;
  if (path) {
    line += `<span class="row-path" aria-hidden="true">·</span><span class="row-path">${escapeHtml(path)}</span>`;
  }
  const ruleHtml = rule ? `<span class="row-rule">${escapeHtml(rule)}</span>` : "";
  return `<a class="catalog-row" href="${escapeHtml(hrefId(gid))}" data-id="${escapeHtml(gid)}" data-container="${escapeHtml(cid)}"${hidden ? " hidden" : ""}><span class="row-line">${line}</span>${ruleHtml}</a>`;
}

function bindCatalog(rows, jobs) {
  const search = document.getElementById("catalog-search");
  const chips = document.getElementById("catalog-chips");
  const list = document.getElementById("catalog-list");
  const shown = document.getElementById("shown-count");
  const pager = document.getElementById("catalog-pager");
  const prev = document.getElementById("page-prev");
  const next = document.getElementById("page-next");
  const pageMeta = document.getElementById("page-meta");
  let container = "";
  if (chips) {
    const on = chips.querySelector('[data-chip][aria-pressed="true"]');
    if (on) container = on.getAttribute("data-chip") || "";
  }
  let page = pager
    ? Math.max(1, parseInt(pager.getAttribute("data-page") || "1", 10) || 1)
    : 1;

  function matching() {
    const q = (search && search.value ? search.value : "").trim().toLowerCase();
    return rows.filter((row) => {
      const cid = rowContainer(row, jobs);
      if (container && cid !== container) return false;
      if (q && !searchBlob(row).includes(q)) return false;
      return true;
    });
  }

  function syncUrl() {
    const params = new URLSearchParams();
    if (container) params.set("container", container);
    const raw = (search && search.value ? search.value : "").trim();
    if (raw) params.set("q", raw);
    if (page > 1) params.set("page", String(page));
    const qs = params.toString();
    const nextUrl = location.pathname + (qs ? "?" + qs : "");
    if (nextUrl !== location.pathname + location.search) {
      history.replaceState(null, "", nextUrl);
    }
  }

  function apply() {
    const matched = matching();
    const total = matched.length;
    const pages = Math.max(1, Math.ceil(total / PAGE_SIZE) || 1);
    if (page > pages) page = pages;
    if (page < 1) page = 1;
    const start = (page - 1) * PAGE_SIZE;
    const end = Math.min(start + PAGE_SIZE, total);
    if (list) {
      list.innerHTML = matched.slice(start, end).map((row) => rowHtml(row, jobs, false)).join("");
    }
    if (shown) shown.textContent = total + " shown";
    if (pageMeta) pageMeta.textContent = pagerMeta(total, page);
    if (pager) pager.setAttribute("data-page", String(page));
    if (prev) prev.disabled = page <= 1 || total === 0;
    if (next) next.disabled = page >= pages || total === 0;
    syncUrl();
  }

  if (search) search.addEventListener("input", () => {
    page = 1;
    apply();
  });
  if (chips) {
    chips.addEventListener("click", (event) => {
      const btn = event.target.closest("[data-chip]");
      if (!btn) return;
      container = btn.getAttribute("data-chip") || "";
      for (const btnChip of chips.querySelectorAll("[data-chip]")) {
        const on = btnChip === btn;
        btnChip.className = on ? "chip chip-on" : "chip";
        btnChip.setAttribute("aria-pressed", on ? "true" : "false");
      }
      page = 1;
      apply();
    });
  }
  if (prev) prev.addEventListener("click", () => {
    page -= 1;
    apply();
  });
  if (next) next.addEventListener("click", () => {
    page += 1;
    apply();
  });
  apply();
}

export async function renderCatalog(root) {
  setTitle("Catalog — Open UX");
  const params = new URLSearchParams(location.search);
  const container = CHIP_IDS.has(params.get("container") || "") ? params.get("container") : "";
  const query = (params.get("q") || "").trim();
  let page = parseInt(params.get("page") || "1", 10);
  if (!Number.isFinite(page) || page < 1) page = 1;
  const hasSsr = root.querySelector('[data-ssr-page="catalog"]');
  if (!hasSsr && !indexCache) {
    root.innerHTML = shell(
      `<main class="page"><p class="lede">Loading catalog…</p></main>`,
      { catalogActive: true, paper: true },
    );
  }
  let data;
  try {
    data = await loadIndex();
  } catch {
    root.innerHTML = shell(
      `
  <main class="page">
    <h1 class="page-title">Catalog</h1>
    <p class="lede">Could not load the catalog. Check your connection and try again.</p>
    <button type="button" class="btn btn-outline" id="catalog-retry">Try again</button>
  </main>`,
      { catalogActive: true, paper: true },
    );
    document.getElementById("catalog-retry")?.addEventListener("click", () => {
      renderCatalog(root);
    });
    return;
  }
  const rows = data.guidelines || [];
  const jobs = data.jobs || { containers: [], cards: [] };
  const valueAttr = query ? ` value="${escapeHtml(query)}"` : "";
  root.innerHTML = shell(
    `
  <main class="page">
    <div class="flex flex-col gap-2">
      <div class="flex items-center justify-between gap-4">
        <h1 class="page-title">Catalog</h1>
        <p class="shown" id="shown-count">${rows.length} shown</p>
      </div>
      <p class="lede">Cited UX rules agents audit against</p>
    </div>
    <div class="field">
      <label class="label" for="catalog-search">Search</label>
      <input class="input" id="catalog-search" type="search" autocomplete="off" spellcheck="false"${valueAttr}>
    </div>
    ${chipsHtml(container)}
    <div class="list" id="catalog-list"></div>
    <div class="pager" id="catalog-pager" data-page="${page}">
      <button type="button" class="btn btn-outline" id="page-prev">Prev</button>
      <p class="pager-meta" id="page-meta"></p>
      <button type="button" class="btn btn-outline" id="page-next">Next</button>
    </div>
  </main>`,
    { catalogActive: true, paper: true },
  );
  bindCatalog(rows, jobs);
}

function lines(value) {
  if (value == null) return [];
  if (Array.isArray(value)) return value.filter(Boolean).map(String);
  const text = String(value).trim();
  return text ? [text] : [];
}

function block(field, label, value, labelClass = "") {
  const items = lines(value);
  if (!items.length) return "";
  const cls = `block-label ${labelClass}`.trim();
  const bodies = items.map((line) => `<p class="block-body">${escapeHtml(line)}</p>`).join("");
  return `<section class="block" data-field="${escapeHtml(field)}"><p class="${cls}">${escapeHtml(label)}</p>${bodies}</section>`;
}

function example(field, kind, label, value) {
  const items = lines(value);
  if (!items.length) return "";
  const bodies = items.map((line) => `<p class="block-body">${escapeHtml(line)}</p>`).join("");
  return `<div class="example-${kind}" data-field="${escapeHtml(field)}"><span class="badge-${kind}">${escapeHtml(label)}</span>${bodies}</div>`;
}

function citationsHtml(guideline) {
  const rows = Array.isArray(guideline.citation) ? guideline.citation : [];
  const items = [];
  for (const row of rows) {
    if (!row || typeof row !== "object") continue;
    const source = String(row.source || "").trim();
    const url = String(row.url || "").trim();
    if (!source && !url) continue;
    const sourceHtml = source ? `<p class="cite-source">${escapeHtml(source)}</p>` : "";
    let urlHtml = "";
    if (url) {
      urlHtml = url.startsWith("https://")
        ? `<a class="cite-url" href="${escapeHtml(url)}">${escapeHtml(url)}</a>`
        : `<p class="cite-url">${escapeHtml(url)}</p>`;
    }
    items.push(`<div class="cite-row">${sourceHtml}${urlHtml}</div>`);
  }
  if (!items.length) return "";
  return `<section class="block" data-field="citation"><p class="block-label">Citations</p><div class="cite-list">${items.join("")}</div></section>`;
}

function treeToggle(kind, title, open) {
  const caret = open ? "▾" : "▸";
  return `<div class="tree-group${open ? " is-open" : ""}"><button type="button" class="tree-item tree-item-${kind}" aria-expanded="${open ? "true" : "false"}"><span class="tree-caret" aria-hidden="true">${caret}</span><span>${escapeHtml(title)}</span></button><div class="tree-children">`;
}

function treeHtml(jobs, index, current) {
  if (!(jobs.containers || []).length) return "";
  const currentId = String(current.id || "");
  const currentContainer = String(current.container || "");
  const currentCard = String(current.card || "");
  const currentFacet = String(current.facet || "");
  const byFacet = new Map();
  for (const row of index) {
    const key = `${row.container || ""}\0${row.card || ""}\0${row.facet || ""}`;
    if (!byFacet.has(key)) byFacet.set(key, []);
    byFacet.get(key).push(row);
  }
  const parts = [`<nav class="sidebar" id="catalog-tree" aria-label="Catalog tree">`];
  for (const container of jobs.containers || []) {
    const openC = container.id === currentContainer;
    parts.push(treeToggle("container", container.title, openC));
    for (const card of jobs.cards || []) {
      if (card.container !== container.id) continue;
      const openCard = openC && card.id === currentCard;
      parts.push(treeToggle("card", card.title, openCard));
      for (const facet of card.facets || []) {
        const openF = openCard && facet.id === currentFacet;
        parts.push(treeToggle("facet", facet.title, openF));
        for (const row of byFacet.get(`${container.id}\0${card.id}\0${facet.id}`) || []) {
          const gid = String(row.id || "");
          if (!gid) continue;
          const active = gid === currentId;
          const cls = "tree-item tree-item-rule" + (active ? " tree-item-on" : "");
          const pip = active ? `<span class="tree-pip" aria-hidden="true"></span>` : "";
          parts.push(
            `<a class="${cls}" href="${escapeHtml(hrefId(gid))}" data-id="${escapeHtml(gid)}">${pip}<span>${escapeHtml(displayName(row))}</span></a>`,
          );
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

function bindTree() {
  const tree = document.getElementById("catalog-tree");
  if (!tree) return;
  tree.addEventListener("click", (event) => {
    const btn = event.target.closest("button.tree-item[aria-expanded]");
    if (!btn || !tree.contains(btn)) return;
    const group = btn.parentElement;
    if (!group || !group.classList.contains("tree-group")) return;
    const next = btn.getAttribute("aria-expanded") !== "true";
    btn.setAttribute("aria-expanded", next ? "true" : "false");
    group.classList.toggle("is-open", next);
    const caret = btn.querySelector(".tree-caret");
    if (caret) caret.textContent = next ? "▾" : "▸";
  });
}

function eyebrow(guideline, jobs) {
  const category = String(guideline.category || "").trim();
  const segment = String(guideline.segment || "").trim();
  let path = "";
  if (category && segment) path = `${category} / ${segment}`;
  else if (category) path = category;
  else path = rowPath(guideline, jobs);
  const severity = String(guideline.severity || "").trim();
  const chip = severity
    ? `<span class="severity" data-field="severity">${escapeHtml(severity[0].toUpperCase() + severity.slice(1))}</span>`
    : "";
  const pathHtml = path ? `<p class="eyebrow-path">${escapeHtml(path)}</p>` : "";
  if (!pathHtml && !chip) return "";
  return `<div class="eyebrow">${pathHtml}${chip}</div>`;
}

function ruleContentHtml(found, jobs) {
  const name = displayName(found);
  const gid = String(found.id || "");
  const fields = [
    `<h1 class="rule-name" data-field="name">${escapeHtml(name)}</h1>`,
    `<p class="rule-id" data-field="id">${escapeHtml(displayId(gid))}</p>`,
  ];
  if (found.rule) {
    fields.push(`<p class="rule-text" data-field="rule">${escapeHtml(found.rule)}</p>`);
  }
  const header = `<div class="flex flex-col gap-2" data-field="header">${eyebrow(found, jobs)}${fields.join("")}</div>`;
  const when = block("apply_when", "When to use", found.apply_when, "block-use");
  const notWhen = block("not_when", "Not when", found.not_when, "block-not");
  const stack = [
    header,
    block("description", "Description", found.description),
    when || notWhen ? `<div class="when-stack">${when}${notWhen}</div>` : "",
    block("agent_hint", "Agent hint", found.agent_hint),
  ];
  const examples =
    example("pass_when", "pass", "Pass", found.pass_when) +
    example("fail_when", "fail", "Fail", found.fail_when);
  if (examples) stack.push(`<div class="examples">${examples}</div>`);
  stack.push(citationsHtml(found));
  return `<a class="back" href="/catalog">← Back to Catalog</a>${stack.join("")}`;
}

function markActiveRule(tree, guidelineId) {
  const want = String(guidelineId || "");
  for (const el of tree.querySelectorAll(".tree-item-rule")) {
    const on = el.getAttribute("data-id") === want;
    el.classList.toggle("tree-item-on", on);
    const pip = el.querySelector(".tree-pip");
    if (on && !pip) {
      el.insertAdjacentHTML("afterbegin", '<span class="tree-pip" aria-hidden="true"></span>');
    } else if (!on && pip) {
      pip.remove();
    }
  }
}

function revealActiveRule(tree, guidelineId) {
  const want = String(guidelineId || "");
  const link = [...tree.querySelectorAll(".tree-item-rule")].find(
    (el) => el.getAttribute("data-id") === want,
  );
  if (!link) return;
  let node = link.parentElement;
  while (node && node !== tree) {
    if (node.classList.contains("tree-group")) {
      node.classList.add("is-open");
      const btn = node.querySelector(":scope > button.tree-item[aria-expanded]");
      if (btn) {
        btn.setAttribute("aria-expanded", "true");
        const caret = btn.querySelector(".tree-caret");
        if (caret) caret.textContent = "▾";
      }
    }
    node = node.parentElement;
  }
}

export function catalogNamesPage(guidelines) {
  const rows = Array.isArray(guidelines) ? guidelines : [];
  const items = rows
    .map((row) => {
      const gid = String(row.id || "");
      if (!gid) return "";
      return `<a href="${escapeHtml(hrefId(gid))}">${escapeHtml(displayName(row))}</a>`;
    })
    .filter(Boolean)
    .join("");
  return {
    title: "Catalog — Open UX",
    description: "Cited UX rules agents audit against",
    body: ssr(
      "catalog",
      shell(
        `
  <main class="page">
    <h1 class="page-title">Catalog</h1>
    <p class="lede">Cited UX rules agents audit against</p>
    <p>${rows.length} shown</p>
    <div class="list">${items}</div>
  </main>`,
        { catalogActive: true, paper: true },
      ),
    ),
  };
}

export function rulePage(found, indexData) {
  const jobs = (indexData && indexData.jobs) || { containers: [], cards: [] };
  const index = (indexData && indexData.guidelines) || [];
  const gid = String(found.id || "");
  const name = displayName(found);
  const rule = String(found.rule || found.description || "").trim();
  return {
    title: `${name} — Open UX`,
    description: rule.split(". ")[0] || name,
    body: ssr(
      "rule",
      shell(
        `
  <div class="rule-shell">
    ${treeHtml(jobs, index, found)}
    <main class="content">
      ${ruleContentHtml(found, jobs)}
    </main>
  </div>`,
        { catalogActive: true, paper: true },
      ),
      { rule: gid },
    ),
  };
}

function paintRulePage(root, found, indexData) {
  root.innerHTML = rulePage(found, indexData).body;
  bindTree();
}

async function fetchGuideline(guidelineId) {
  const itemRes = await fetch("/api/catalog/" + encodeURIComponent(guidelineId));
  if (itemRes.status === 404) return null;
  if (!itemRes.ok) throw new Error("guideline");
  const found = await itemRes.json();
  if (!found || found.found === false) return null;
  return found;
}

export async function renderRule(root, guidelineId) {
  const gen = ++ruleGen;
  const prerendered = root.querySelector("[data-ssr-rule]");
  const hasSsr = prerendered && prerendered.getAttribute("data-ssr-rule") === guidelineId;
  const tree = root.querySelector("#catalog-tree");
  const content = root.querySelector("main.content");
  const canReuse = Boolean(tree && content && root.querySelector(".rule-shell"));

  if (canReuse) {
    let found;
    try {
      found = await fetchGuideline(guidelineId);
    } catch {
      if (gen !== ruleGen) return;
      renderServerError(root);
      return;
    }
    if (gen !== ruleGen) return;
    if (!found) {
      renderNotFound(root, guidelineId, { kind: "rule" });
      return;
    }
    const jobs = (indexCache && indexCache.jobs) || { containers: [], cards: [] };
    setTitle(`${displayName(found)} — Open UX`);
    content.innerHTML = ruleContentHtml(found, jobs);
    markActiveRule(tree, String(found.id || guidelineId));
    revealActiveRule(tree, String(found.id || guidelineId));
    return;
  }

  if (!hasSsr) {
    setTitle("Catalog — Open UX");
    root.innerHTML = shell(
      `<div class="rule-shell"><main class="content"><p class="lede">Loading rule…</p></main></div>`,
      { catalogActive: true, paper: true },
    );
  }

  let found;
  try {
    found = await fetchGuideline(guidelineId);
  } catch {
    if (gen !== ruleGen) return;
    renderServerError(root);
    return;
  }
  if (gen !== ruleGen) return;
  if (!found) {
    renderNotFound(root, guidelineId, { kind: "rule" });
    return;
  }

  const jobs = (indexCache && indexCache.jobs) || { containers: [], cards: [] };
  setTitle(`${displayName(found)} — Open UX`);
  if (indexCache) {
    paintRulePage(root, found, indexCache);
    return;
  }

  const liveContent = root.querySelector("main.content");
  if (liveContent) {
    liveContent.innerHTML = ruleContentHtml(found, jobs);
  }

  let indexData;
  try {
    indexData = await loadIndex();
  } catch {
    return;
  }
  if (gen !== ruleGen) return;
  paintRulePage(root, found, indexData);
}
