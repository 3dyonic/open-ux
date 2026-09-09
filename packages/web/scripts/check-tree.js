import { crumbParts, locate } from "../src/catalog-model.js";
import { treeHtml } from "../src/tree.js";

function fail(message) {
  console.error(message);
  process.exitCode = 1;
}

function count(hay, needle) {
  return hay.split(needle).length - 1;
}

function buttonClass(html, kind, id) {
  const match = html.match(
    new RegExp(
      `data-tree="${kind}" data-id="${id}"><button type="button" class="([^"]+)"`,
    ),
  );
  return match ? match[1] : "";
}

function leafInner(html, id) {
  const match = html.match(new RegExp(`data-id="${id}"[^>]*>([\\s\\S]*?)</a>`));
  return match ? match[1] : "";
}

const jobs = {
  containers: [
    { id: "c1", title: "Container One" },
    { id: "c-empty", title: "Empty Container" },
  ],
  cards: [
    {
      id: "card-a",
      title: "Card A",
      container: "c1",
      facets: [
        { id: "facet-a", title: "Facet A" },
        { id: "facet-empty", title: "Empty Facet" },
        { id: "facet-b", title: "Facet B" },
      ],
    },
    {
      id: "card-b",
      title: "Card B",
      container: "c1",
      facets: [{ id: "facet-c", title: "Facet C" }],
    },
  ],
};

const index = [
  {
    id: "rule.first",
    name: "First leaf",
    container: "c1",
    card: "card-a",
    facet: "facet-a",
  },
  {
    id: "rule.last",
    name: "Last leaf",
    container: "c1",
    card: "card-a",
    facet: "facet-a",
  },
  {
    id: "rule.b",
    name: "Other card leaf",
    container: "c1",
    card: "card-b",
    facet: "facet-c",
  },
  {
    id: "rule.sibling-facet",
    name: "Sibling facet leaf",
    container: "c1",
    card: "card-a",
    facet: "facet-b",
  },
  { id: "rule.orphan", name: "Orphan leaf", container: "c1", card: "card-a" },
];

if (treeHtml({ containers: [], cards: [] }, index, { id: "rule.last" }) !== "") {
  fail("empty jobs must render no tree");
}

const html = treeHtml(jobs, index, {
  id: "rule.last",
  card: "card-a",
  facet: "facet-a",
});

if (!html.includes('id="catalog-tree"')) fail("tree nav missing");
if (html.includes("Empty Container")) fail("container with no rules must be omitted");
if (html.includes("Empty Facet")) fail("facet with no rules must be omitted");
if (html.includes("Orphan leaf")) fail("row without a facet must be omitted");
if (!html.includes("Facet B")) fail("sibling facet on the current card must still render");
if (!html.includes("Card B")) fail("sibling card must still render");

if (count(html, "is-current") !== 1) fail("exactly one current leaf");
if (count(html, 'aria-current="page"') !== 1) fail("exactly one aria-current page");

const lastInner = leafInner(html, "rule.last");
const firstInner = leafInner(html, "rule.first");
if (!lastInner.includes("tree-caret-leaf")) fail("last leaf must keep a caret column");
if (!firstInner.includes("tree-caret-leaf")) fail("first leaf must keep the same caret column");
if (lastInner.includes("tree-pip") || firstInner.includes("tree-pip")) fail("leaves must not include a pip");
if (html.includes("tree-pip")) fail("tree must not include a pip");
if (!html.includes("tree-caret-icon")) fail("groups must use the caret icon");
if (leafInner(html, "rule.last").length === 0) fail("last leaf missing");
if (!html.includes('data-id="rule.last"') || !html.includes("tree-rule is-current")) {
  fail("last leaf must be the current page");
}
if (html.includes("tree-rule is-current") && html.includes('data-id="rule.first"')) {
  const firstBtn = html.match(/data-id="rule.first"[^>]*/);
  if (firstBtn && firstBtn[0].includes("is-current")) fail("first leaf must not be current");
}

const containerA = buttonClass(html, "container", "c1");
const cardA = buttonClass(html, "card", "card-a");
const cardB = buttonClass(html, "card", "card-b");
const facetA = buttonClass(html, "facet", "facet-a");
const facetB = buttonClass(html, "facet", "facet-b");
if (!containerA.includes("is-here")) fail("container with the active leaf must be is-here");
if (!cardA.includes("is-here")) fail("current card must be is-here");
if (cardA.includes("is-current")) fail("cards must not use is-current");
if (cardB.includes("is-here")) fail("sibling card must not be is-here");
if (cardB.includes("is-current")) fail("sibling card must not be current");
if (!facetA.includes("is-here")) fail("current facet must be is-here");
if (facetA.includes("is-current")) fail("facets must not use is-current");
if (facetB.includes("is-here")) fail("sibling facet must not be is-here");

if (!html.includes('class="tree-group is-open" data-tree="facet" data-id="facet-a"')) {
  fail("current facet must start open");
}
if (html.includes('class="tree-group is-open" data-tree="facet" data-id="facet-b"')) {
  fail("sibling facet must start closed");
}
if (html.includes('class="tree-group is-open" data-tree="card" data-id="card-b"')) {
  fail("sibling card must start closed");
}
if (count(html, "tree-container is-here") !== 1) fail("exactly one here container");
if (count(html, 'class="tree-group is-open" data-tree="container"') !== 1) {
  fail("exactly one open container");
}
if (count(html, 'class="tree-group is-open" data-tree="card"') !== 1) {
  fail("exactly one open card");
}
if (count(html, 'class="tree-group is-open" data-tree="facet"') !== 1) {
  fail("exactly one open facet");
}
if (count(html, "tree-card is-here") !== 1) fail("exactly one here card");
if (count(html, "tree-facet is-here") !== 1) fail("exactly one here facet");

if (html.includes("tree-item-on")) fail("legacy tree-item-on must not ship");
if (html.includes("tree-item-rule") || html.includes("tree-item-card")) {
  fail("legacy tree-item-* names must not ship");
}

const fromIndex = locate({ id: "rule.last" }, jobs, index);
if (fromIndex.container !== "c1" || fromIndex.card !== "card-a" || fromIndex.facet !== "facet-a") {
  fail("locate must fill the path from the index when the row only has an id");
}

const crumbs = crumbParts({ id: "rule.last", card: "card-a", facet: "facet-a" }, jobs);
if (crumbs.join(" / ") !== "Container One / Card A / Facet A") {
  fail(`crumb path was ${crumbs.join(" / ")}`);
}

const fallback = crumbParts(
  { container: "c1", card: "card-a", facet: "facet-a" },
  { containers: [], cards: [] },
);
if (fallback.join(" / ") !== "c1 / card-a / facet-a") {
  fail("crumb path must fall back to ids when jobs titles are missing");
}

if (treeHtml(jobs, [], { id: "x" }).includes("tree-rule")) {
  fail("empty index must not invent leaves");
}

if (process.exitCode) {
  console.error("catalog tree checks failed");
} else {
  console.log("catalog tree checks passed");
}
