/** Helpers for the docs collection: URLs, navigation order and the Markdown exports. */
import { getCollection, type CollectionEntry } from "astro:content";
import { sidebarOrder } from "../data/site.mjs";

export type DocPage = CollectionEntry<"docs">;

/** Commands rendered by <SetupNodeCurl /> and <RestoreCurl /> (as on docs.scrt.network). */
export const commands = {
  setup:
    "curl -fsSL https://docs.scrt.network/secret-setup.py -o secret-setup.py && curl -fsSL https://docs.scrt.network/restore.sh -o restore.sh && python3 secret-setup.py",
  restore:
    "curl -fsSL -H 'Cache-Control: no-cache' -o restore.sh \"https://docs.scrt.network/restore.sh?t=$(date +%s)\" && bash restore.sh",
};

export const pageUrl = (slug: string) => (slug === "index" ? "/" : `/${slug}`);
export const mdUrl = (slug: string) => (slug === "index" ? "/index.md" : `/${slug}/index.md`);
export const mdxUrl = (slug: string) => (slug === "index" ? "/index.mdx" : `/${slug}/index.mdx`);

export async function getPages(): Promise<Map<string, DocPage>> {
  const pages = await getCollection("docs");
  return new Map(pages.map((p) => [p.id, p]));
}

/** Page ids in sidebar order (from src/data/site.mjs). */
export const pageOrder = (): string[] => sidebarOrder();

/** The page as Markdown, in the format docs.scrt.network serves at …/index.md. */
export function toMarkdown(page: DocPage, site: URL): string {
  const body = (page.body ?? "")
    .replace(/<SetupNodeCurl\s*\/>/g, "```bash\n" + commands.setup + "\n```")
    .replace(/<RestoreCurl\s*\/>/g, "```bash\n" + commands.restore + "\n```")
    .replace(/<p>\{("(?:[^"\\]|\\.)*")\}<\/p>/g, (_, s) => JSON.parse(s))
    .replace(
      /<Flowchart\s+label="([^"]*)"\s+chart=\{`([\s\S]*?)`\}\s*\/>/g,
      (_, label, chart) => `${label}\n\n\`\`\`mermaid\n${chart.trim()}\n\`\`\``,
    )
    .replace(/<Tabs[^>]*>([\s\S]*?)<\/Tabs>/g, (_, inner: string) =>
      inner
        .replace(/\s*<\/TabItem>/g, "")
        .replace(/^\s*<TabItem label="([^"]*)">/gm, "### $1\n")
        .replace(/^ {4}/gm, "")
        .trim(),
    )
    .trim();
  const url = (p: string) => new URL(p, site).href;
  return [
    "---",
    `title: ${JSON.stringify(page.data.title)}`,
    `description: ${JSON.stringify(page.data.description)}`,
    "---",
    "",
    "> Documentation Index",
    `> Fetch the complete documentation index at: ${url("/llms.txt")}`,
    "> Use this file to discover all available pages before exploring further.",
    "",
    `# ${page.data.title}`,
    "",
    body,
    "",
    `Source: ${url(mdxUrl(page.id))}`,
    "",
  ].join("\n");
}

/** The original MDX source of the page. */
export function toMdx(page: DocPage): string {
  return [
    "---",
    `title: ${JSON.stringify(page.data.title)}`,
    `description: ${JSON.stringify(page.data.description)}`,
    "---",
    "",
    (page.body ?? "").trim(),
    "",
  ].join("\n");
}
