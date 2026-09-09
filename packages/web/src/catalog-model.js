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

export function hrefId(guidelineId) {
  return "/catalog/" + encodeURIComponent(guidelineId).replace(/%2E/g, ".");
}

export function cardById(jobs, cardId) {
  return (jobs.cards || []).find((card) => card.id === cardId) || null;
}

export function containerTitle(jobs, containerId) {
  if (!containerId) return "";
  const found = (jobs.containers || []).find((item) => item.id === containerId);
  return found ? found.title : containerId;
}

export function cardTitle(jobs, cardId) {
  if (!cardId) return "";
  const card = cardById(jobs, cardId);
  return card ? card.title : cardId;
}

export function facetTitle(jobs, cardId, facetId) {
  if (!facetId) return "";
  const card = cardById(jobs, cardId);
  const local = (card?.facets || []).find((facet) => facet.id === facetId);
  if (local) return local.title;
  for (const item of jobs.cards || []) {
    const hit = (item.facets || []).find((facet) => facet.id === facetId);
    if (hit) return hit.title;
  }
  return String(facetId);
}

function containerFromFacet(jobs, facetId) {
  if (!facetId) return "";
  for (const item of jobs.cards || []) {
    if ((item.facets || []).some((facet) => facet.id === facetId)) {
      return String(item.container || "");
    }
  }
  return "";
}

export function locate(row, jobs = { containers: [], cards: [] }, index = []) {
  const id = String(row?.id || "").trim();
  const listed = (index || []).find((item) => String(item.id || "") === id) || {};
  let container = String(row?.container || listed.container || "").trim();
  let card = String(row?.card || listed.card || "").trim();
  let facet = String(row?.facet || listed.facet || "").trim();
  if (!container && card) {
    const found = cardById(jobs, card);
    if (found?.container) container = String(found.container);
  }
  if (!container && facet) container = containerFromFacet(jobs, facet);
  if (!card && facet) {
    for (const item of jobs.cards || []) {
      if ((item.facets || []).some((entry) => entry.id === facet)) {
        card = String(item.id || "");
        if (!container && item.container) container = String(item.container);
        break;
      }
    }
  }
  return { id, container, card, facet };
}

export function rowContainer(row, jobs) {
  return locate(row, jobs).container;
}

export function rowPath(row, jobs) {
  const here = locate(row, jobs);
  const left = containerTitle(jobs, here.container);
  const right = cardTitle(jobs, here.card);
  if (left && right) return `${left} / ${right}`;
  return left || right;
}

export function crumbParts(row, jobs) {
  const here = locate(row, jobs);
  return [
    containerTitle(jobs, here.container),
    cardTitle(jobs, here.card),
    facetTitle(jobs, here.card, here.facet),
  ].filter(Boolean);
}
