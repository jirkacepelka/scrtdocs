/**
 * Site settings and the sidebar, shared by astro.config.mjs (Starlight) and the Markdown and
 * llms.txt exports in src/pages/.
 *
 * Content, navigation, labels and the license are taken from docs.scrt.network (read
 * 2026-10-28). Social links match scrt.network's footer.
 */

export const site = {
  title: "Docs",
  description: "Run a Secret Network node on secret-4 and learn how Secret Zone works.",
  url: process.env.SITE_URL ?? "https://docs.scrt.network",
  mainSite: "https://scrt.network",
  publisher: { name: "Secret³ Dev", href: "https://secret3.dev" },
  license: { name: "AGPL-3.0", href: "https://www.gnu.org/licenses/agpl-3.0.html" },
};

/**
 * Starlight `social` entries (shown in the header and the footer).
 * @type {NonNullable<import("@astrojs/starlight/types").StarlightUserConfig["social"]>}
 */
export const social = [
  { icon: "x.com", label: "X", href: "https://x.com/secretrebooted" },
  { icon: "telegram", label: "Telegram", href: "https://t.me/SCRTCommunity" },
  { icon: "discourse", label: "Forum", href: "https://forum.scrt.network" },
  { icon: "github", label: "GitHub", href: "https://github.com/Secret3dev/SecretNetwork" },
  { icon: "youtube", label: "YouTube", href: "https://www.youtube.com/@SecretNetwork" },
];

/**
 * Starlight sidebar, in docs.scrt.network's order. `slug` is the page id in
 * src/content/docs ("index" is the home page). Top-level groups are the two sections.
 * @type {NonNullable<import("@astrojs/starlight/types").StarlightUserConfig["sidebar"]>}
 */
export const sidebar = [
  {
    label: "Secret Nodes",
    items: [
      { label: "Quick Setup", slug: "index" },
      {
        label: "Hardware",
        collapsed: true,
        items: [{ slug: "operators/requirements" }, { slug: "operators/boards" }],
      },
      {
        label: "Manual",
        items: [
          { slug: "operators/sgx" },
          { slug: "operators/install" },
          { slug: "operators/home" },
          { slug: "operators/register" },
          { slug: "operators/allowlist" },
          { slug: "operators/full-node" },
        ],
      },
      {
        label: "Node types",
        collapsed: true,
        items: [{ slug: "operators/archive" }, { slug: "operators/validator" }],
      },
      { label: "Other parts", collapsed: true, items: [{ slug: "operators/rpc-lcd" }] },
      {
        label: "Upgrade",
        collapsed: true,
        items: [
          { label: "Overview", slug: "operators/upgrade" },
          { label: "1.27.3", slug: "operators/upgrade/v1.27.3" },
          { label: "1.27.2", slug: "operators/upgrade/v1.27.2" },
        ],
      },
    ],
  },
  {
    label: "Secret Zone",
    badge: { text: "Draft", variant: "caution" },
    collapsed: true,
    items: [
      { label: "Overview", slug: "secret-zone" },
      { slug: "secret-zone/user-journey" },
      { slug: "secret-zone/builder-journey" },
      { slug: "secret-zone/programs-and-sdk" },
      { slug: "secret-zone/network-programs" },
    ],
  },
];

/** Section tabs in the header: the first page of each top-level group. */
export const sections = [
  { label: "Secret Nodes", href: "/", match: (path) => !path.startsWith("/secret-zone") },
  { label: "Secret Zone", href: "/secret-zone/", match: (path) => path.startsWith("/secret-zone") },
];

/** Every page slug in sidebar order. */
/** @returns {string[]} */
export function sidebarOrder(items = /** @type {any[]} */ (sidebar)) {
  return items.flatMap((item) => (item.items ? sidebarOrder(item.items) : [item.slug]));
}
