/**
 * Site settings, footer links and the navigation tree.
 *
 * Content, navigation, labels and the license are taken from docs.scrt.network (read
 * 2026-10-28). Social links match scrt.network's footer.
 */

export const site = {
  name: "Secret Network Docs",
  description: "Run a Secret Network node on secret-4 and learn how Secret Zone works.",
  ogImage: "/og-default.png",
  mainSite: "https://scrt.network",
  publisher: { name: "Secret³ Dev", href: "https://secret3.dev" },
  license: { name: "AGPL-3.0", href: "https://www.gnu.org/licenses/agpl-3.0.html" },
} as const;

export const socialLinks = [
  { label: "X (Twitter)", href: "https://x.com/secretrebooted", icon: "ph:x-logo" },
  { label: "Telegram", href: "https://t.me/SCRTCommunity", icon: "ph:telegram-logo" },
  { label: "Forum", href: "https://forum.scrt.network", icon: "ph:chats-circle" },
  { label: "GitHub", href: "https://github.com/Secret3dev/SecretNetwork", icon: "ph:github-logo" },
  { label: "YouTube", href: "https://www.youtube.com/@SecretNetwork", icon: "ph:youtube-logo" },
] as const;

/** A link to a page, by its slug. `label` overrides the page title in the sidebar. */
export interface NavPage {
  slug: string;
  label?: string;
}
/** A collapsible group. With `slug`, the group name itself links to a page. */
export interface NavGroup {
  group: string;
  slug?: string;
  items: NavPage[];
}
export interface NavSection {
  title: string;
  /** First page of the section, used by the header tabs. */
  slug: string;
  /** Section of the Secret 2.0 draft design: shown with a Draft badge. */
  draft?: boolean;
  items: (NavPage | NavGroup)[];
}

export const nav: NavSection[] = [
  {
    title: "Secret Nodes",
    slug: "index",
    items: [
      { slug: "index", label: "Quick Setup" },
      {
        group: "Hardware",
        items: [{ slug: "operators/requirements" }, { slug: "operators/boards" }],
      },
      {
        group: "Manual",
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
        group: "Node types",
        items: [{ slug: "operators/archive" }, { slug: "operators/validator" }],
      },
      { group: "Other parts", items: [{ slug: "operators/rpc-lcd" }] },
      {
        group: "Upgrade",
        slug: "operators/upgrade",
        items: [
          { slug: "operators/upgrade/v1.27.3", label: "1.27.3" },
          { slug: "operators/upgrade/v1.27.2", label: "1.27.2" },
        ],
      },
    ],
  },
  {
    title: "Secret Zone",
    slug: "secret-zone",
    draft: true,
    items: [
      { slug: "secret-zone" },
      { slug: "secret-zone/user-journey" },
      { slug: "secret-zone/builder-journey" },
      { slug: "secret-zone/programs-and-sdk" },
      { slug: "secret-zone/network-programs" },
    ],
  },
];
