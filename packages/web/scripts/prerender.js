import { readdir, readFile, mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { catalogNamesPage, rulePage } from "../src/catalog.js";
import { notFoundPage, serverErrorPage } from "../src/errors.js";
import { healthPage } from "../src/health.js";
import { invitePage, redeemPage, requestedPage } from "../src/invite.js";
import { landingPage } from "../src/landing.js";
import { privacyPage } from "../src/privacy.js";
import { sourcesPage } from "../src/sources.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(here, "..");
const dist = path.join(webRoot, "dist");
const catalogRoot = process.env.OPEN_UX_CATALOG
  ? path.resolve(process.env.OPEN_UX_CATALOG)
  : path.resolve(webRoot, "../../catalog");

function escapeAttr(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;");
}

function fill(template, page) {
  let html = template.replace(
    /<div id="app"><\/div>/,
    `<div id="app">${page.body}</div>`,
  );
  html = html.replace(/<title>[^<]*<\/title>/, `<title>${escapeAttr(page.title)}</title>`);
  html = html.replace(
    /<meta name="description" content="[^"]*">/,
    `<meta name="description" content="${escapeAttr(page.description)}">`,
  );
  return html;
}

async function writePage(rel, template, page) {
  const dest = path.join(dist, rel);
  await mkdir(path.dirname(dest), { recursive: true });
  await writeFile(dest, fill(template, page));
}

async function walkJson(dir, out) {
  let entries;
  try {
    entries = await readdir(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) await walkJson(full, out);
    else if (entry.name.endsWith(".json")) {
      out.push(JSON.parse(await readFile(full, "utf8")));
    }
  }
}

function jobsPayload(raw) {
  return {
    containers: (raw.containers || []).map((row) => ({
      id: row.id,
      title: row.title,
    })),
    cards: (raw.cards || []).map((card) => ({
      id: card.id,
      title: card.title,
      container: card.container,
      facets: (card.facets || []).map((facet) => ({
        id: facet.id,
        title: facet.title,
      })),
    })),
  };
}

const template = await readFile(path.join(dist, "index.html"), "utf8");
const index = JSON.parse(await readFile(path.join(catalogRoot, "index.json"), "utf8"));
const jobs = jobsPayload(
  JSON.parse(await readFile(path.join(catalogRoot, "jobs.json"), "utf8")),
);
const guidelines = [];
await walkJson(path.join(catalogRoot, "rules"), guidelines);
const indexData = { guidelines: index.guidelines || [], jobs };

await writePage("index.html", template, landingPage());
await writePage("catalog/index.html", template, catalogNamesPage(index.guidelines || []));
for (const found of guidelines) {
  const id = String(found.id || "");
  if (!id) continue;
  await writePage(`catalog/${id}/index.html`, template, rulePage(found, indexData));
}
await writePage("privacy/index.html", template, privacyPage());
await writePage("sources/index.html", template, sourcesPage());
await writePage("health/index.html", template, healthPage());
await writePage("invite/index.html", template, invitePage());
await writePage("invite/requested/index.html", template, requestedPage());
await writePage("invite/redeem/index.html", template, redeemPage());
await writePage("404.html", template, notFoundPage("{{detail}}", { kind: "page" }));
await writePage("404-rule.html", template, notFoundPage("{{detail}}", { kind: "rule" }));
await writePage("500.html", template, serverErrorPage("{{path}}"));

console.log(`prerendered ${guidelines.length} rules into ${dist}`);
