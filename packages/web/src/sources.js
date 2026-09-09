import { shell } from "./chrome.js";
import { escapeHtml, setTitle, ssr } from "./util.js";

const CONTACT = "contact@open-ux.dev";

const SECTIONS = [
  [
    "What a rule is",
    [
      "Each file is one claim. It has a pass/fail, and a citation that names the original page and links to it. Extra URLs on that citation are more sources for the same claim, not extra claims.",
    ],
    [],
  ],
  [
    "How we write it",
    [
      "We read published design-system and UX guidance that is already public. We write our own short pass/fail so an agent can apply the claim. We do not republish the original page.",
      "If a claim has no honest home on a Situation Card, we leave it out. Empty leaves stay empty; we do not invent criteria for them.",
    ],
    [],
  ],
  [
    "Licenses",
    [
      "Open UX (the catalog files, tools, and this site) is MIT. That license is ours. It does not cover the original design systems.",
      "The organizations we cite keep their own copyrights and licenses. Linking to them is not an endorsement, and we are not those organizations.",
    ],
    [],
  ],
  [
    "Ask us to change or remove a rule",
    [
      "If you are the source, or you believe a rule should not be in the catalog, email contact@open-ux.dev.",
      "Include:",
    ],
    [
      "the rule id (for example govuk.hide-password-by-default-show-toggle)",
      "the catalog or citation URL",
      "what you want (remove the file, drop a citation, or correct the paraphrase)",
      "who you are in relation to the source",
    ],
  ],
  ["Contact", [], []],
];

function withMail(text) {
  const escaped = escapeHtml(text);
  return escaped.replaceAll(
    escapeHtml(CONTACT),
    `<a class="underline" href="mailto:${CONTACT}">${escapeHtml(CONTACT)}</a>`,
  );
}

function sectionHtml([heading, paragraphs, items]) {
  let body = "";
  if (heading === "Contact") {
    body = `<p class="m-0 text-[15px] leading-[22px] text-ink">Sources and catalog questions: <a class="underline" href="mailto:${CONTACT}">${escapeHtml(CONTACT)}</a>. For waitlist email, keys, and analytics, see <a class="underline" href="/privacy">Privacy</a>.</p>`;
  } else {
    body = paragraphs
      .map(
        (item) =>
          `<p class="m-0 text-[15px] leading-[22px] text-ink">${withMail(item)}</p>`,
      )
      .join("");
  }
  const list = items.length
    ? `<ul class="m-0 flex flex-col gap-2.5 pl-5">${items
        .map((item) => `<li class="m-0 text-[15px] leading-[22px] text-ink">${escapeHtml(item)}</li>`)
        .join("")}</ul>`
    : "";
  const closing =
    heading === "Ask us to change or remove a rule"
      ? `<p class="m-0 text-[15px] leading-[22px] text-ink">${escapeHtml(
          "We will look at it and reply. We may remove the file, rewrite the paraphrase, or keep it if the citation still supports the claim.",
        )}</p>`
      : "";
  return `<section class="flex flex-col gap-3"><h2 class="m-0 text-base font-semibold text-ink">${escapeHtml(heading)}</h2>${body}${list}${closing}</section>`;
}

export function sourcesPage() {
  return {
    title: "Sources — Open UX",
    description:
      "How Open UX writes catalog rules, and how to ask us to change or remove one.",
    body: ssr(
      "sources",
      shell(
        `
  <main class="page page-sources">
    <h1 class="page-title">Sources</h1>
    <p class="lede">How Open UX writes catalog rules, and how to ask us to change or remove one.</p>
    ${SECTIONS.map(sectionHtml).join("")}
  </main>`,
        {},
      ),
    ),
  };
}

export function renderSources(root) {
  const page = sourcesPage();
  setTitle(page.title);
  if (root.querySelector('[data-ssr-page="sources"]')) return;
  root.innerHTML = page.body;
}
