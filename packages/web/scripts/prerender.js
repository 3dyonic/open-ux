import { readdir, readFile, mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { adminPage } from "../src/admin.js";
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

const ORIGIN = "https://open-ux.dev";
const SITE_NAME = "Open UX";
const SITE_DESCRIPTION =
  "Stop inventing UX rules from memory. Open UX is a shared, cited catalog agents list, fetch, and audit against.";
const ICON = `${ORIGIN}/icon.png`;
const HEAD_START = "<!-- open-ux:head:start -->";
const HEAD_END = "<!-- open-ux:head:end -->";

function escapeAttr(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;");
}

function canonicalFor(pagePath) {
  const text = pagePath && pagePath.startsWith("/") ? pagePath : `/${pagePath || ""}`;
  if (text === "/" || text === "") return `${ORIGIN}/`;
  return `${ORIGIN}${text.endsWith("/") ? text.slice(0, -1) : text}`;
}

function jsonLd(data) {
  return JSON.stringify(data).replace(/</g, "\\u003c");
}

function siteGraph() {
  return {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "Organization",
        "@id": `${ORIGIN}/#org`,
        name: SITE_NAME,
        url: `${ORIGIN}/`,
        logo: ICON,
        sameAs: ["https://github.com/3dyonic/open-ux"],
        description: SITE_DESCRIPTION,
      },
      {
        "@type": "WebSite",
        "@id": `${ORIGIN}/#website`,
        name: SITE_NAME,
        url: `${ORIGIN}/`,
        publisher: { "@id": `${ORIGIN}/#org` },
        description: SITE_DESCRIPTION,
      },
    ],
  };
}

function breadcrumbList(crumbs) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: crumbs.map((crumb, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: crumb.name,
      item: canonicalFor(crumb.path),
    })),
  };
}

function headTags(page) {
  const indexable = page.index !== false;
  const url = canonicalFor(page.path || "/");
  const title = escapeAttr(page.title);
  const description = escapeAttr(page.description);
  const tags = [];
  if (indexable) {
    tags.push(
      `<link rel="canonical" href="${escapeAttr(url)}">`,
      '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">',
    );
  } else {
    tags.push('<meta name="robots" content="noindex, nofollow">');
  }
  tags.push(
    `<meta property="og:site_name" content="${SITE_NAME}">`,
    '<meta property="og:locale" content="en_US">',
    '<meta property="og:type" content="website">',
    `<meta property="og:title" content="${title}">`,
    `<meta property="og:description" content="${description}">`,
    `<meta property="og:url" content="${escapeAttr(url)}">`,
    `<meta property="og:image" content="${ICON}">`,
    '<meta property="og:image:type" content="image/png">',
    '<meta property="og:image:width" content="512">',
    '<meta property="og:image:height" content="512">',
    `<meta property="og:image:alt" content="${SITE_NAME}">`,
    '<meta name="twitter:card" content="summary">',
    `<meta name="twitter:title" content="${title}">`,
    `<meta name="twitter:description" content="${description}">`,
    `<meta name="twitter:image" content="${ICON}">`,
    `<meta name="twitter:image:alt" content="${SITE_NAME}">`,
  );
  if (indexable) {
    if ((page.path || "/") === "/") {
      tags.push(`<script type="application/ld+json">${jsonLd(siteGraph())}</script>`);
    }
    if (page.breadcrumbs && page.breadcrumbs.length) {
      tags.push(
        `<script type="application/ld+json">${jsonLd(breadcrumbList(page.breadcrumbs))}</script>`,
      );
    }
  }
  return tags.join("\n  ");
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
  const start = html.indexOf(HEAD_START);
  const end = html.indexOf(HEAD_END);
  if (start !== -1 && end !== -1) {
    html =
      html.slice(0, start) +
      `${HEAD_START}\n  ${headTags(page)}\n  ${HEAD_END}` +
      html.slice(end + HEAD_END.length);
  }
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
await writePage("admin/index.html", template, adminPage());
await writePage("404.html", template, notFoundPage("{{detail}}", { kind: "page" }));
await writePage("404-rule.html", template, notFoundPage("{{detail}}", { kind: "rule" }));
await writePage("500.html", template, serverErrorPage("{{path}}"));

console.log(`prerendered ${guidelines.length} rules into ${dist}`);
