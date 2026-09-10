import { shell } from "./chrome.js";
import { escapeHtml, setTitle, ssr } from "./util.js";

const SECTIONS = [
  [
    "What this product is",
    "Open UX is a shared, cited catalog of UX rules. Agents connect with an API key. People can browse the public catalog pages and request access.",
    [],
  ],
  [
    "Analytics (this website)",
    "On public pages (home, catalog, invite request, this privacy page, and sources) we may use Google Tag Manager and Google Analytics to understand traffic.",
    [
      "These load only after you Accept the cookie banner.",
      "If you Decline, we do not load them for that choice.",
      "Cookie settings in the footer opens the banner again.",
      "We do not put analytics on the agent API (/mcp) or admin tools.",
    ],
  ],
  [
    "Waitlist and API keys",
    "",
    [
      "If you request access, we store the email you give us to approve and issue an invite.",
      "After you redeem, you get an API key (uxmcp_…). We store a hash of the key, not the secret itself. The full key is shown once at redeem.",
      "Invite tokens are one-time and stored as hashes with expiry.",
    ],
  ],
  [
    "What we do not store from agent use",
    "When agents call the tools, we do not store UI files, prompts, or other raw content you send for review. Hosted logs may keep high-level usage (for example which tools ran and which rule ids were involved), keyed by a hash of your API key — not by the secret key itself.",
    [],
  ],
  [
    "Retention",
    "Hosted account and usage records are kept only as long as needed to run the service (on the order of weeks, not forever). You can ask us to delete your waitlist email and keys.",
    [],
  ],
  [
    "Self-host",
    "If you run Open UX yourself, this hosted privacy page does not apply — your process, your logs. Analytics and waitlist are hosted-only.",
    [],
  ],
  ["Contact", "", []],
];

const CONTACT = "contact@open-ux.dev";

function sectionHtml([heading, paragraph, bullets]) {
  let body = "";
  if (heading === "Contact") {
    body = `<p class="m-0 text-[15px] leading-[22px] text-ink">Privacy questions: <a class="underline" href="mailto:${CONTACT}">${escapeHtml(CONTACT)}</a>. To ask us to drop a catalog rule, see <a class="underline" href="/sources">Sources</a>.</p>`;
  } else if (paragraph) {
    body = `<p class="m-0 text-[15px] leading-[22px] text-ink">${escapeHtml(paragraph)}</p>`;
  }
  const list = bullets.length
    ? `<ul class="m-0 flex flex-col gap-2.5 pl-5">${bullets.map((item) => `<li class="m-0 text-[15px] leading-[22px] text-ink">${escapeHtml(item)}</li>`).join("")}</ul>`
    : "";
  return `<section class="flex flex-col gap-3"><h2 class="m-0 text-base font-semibold text-ink">${escapeHtml(heading)}</h2>${body}${list}</section>`;
}

export function privacyPage() {
  return {
    title: "Privacy — Open UX",
    description:
      "How Open UX handles waitlist email, API keys, analytics, and agent usage on the hosted service.",
    path: "/privacy",
    body: ssr(
      "privacy",
      shell(
        `
  <main class="page page-privacy">
    <h1 class="page-title">Privacy</h1>
    <p class="lede">How Open UX handles information on the hosted service at open-ux.dev.</p>
    ${SECTIONS.map(sectionHtml).join("")}
  </main>`,
        {},
      ),
    ),
  };
}

export function renderPrivacy(root) {
  const page = privacyPage();
  setTitle(page.title);
  if (root.querySelector('[data-ssr-page="privacy"]')) return;
  root.innerHTML = page.body;
}
