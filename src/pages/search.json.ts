/** Search index for the search dialog: one entry per page, from its Markdown export. */
import type { APIRoute } from "astro";
import { flatNav, getPages, pageUrl, toMarkdown } from "../lib/docs";

const plain = (md: string) =>
  md
    .replace(/^---[\s\S]*?---/, "")
    .replace(/^>.*$/gm, "")
    .replace(/^Source: .*$/m, "")
    .replace(/`([^`]*)`/g, "$1")
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/[#*_>|]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

export const GET: APIRoute = async ({ site }) => {
  const pages = await getPages();
  const entries = flatNav(pages).map((e) => {
    const page = pages.get(e.slug)!;
    return {
      url: pageUrl(e.slug),
      title: page.data.title,
      section: e.group ? `${e.section.title} / ${e.group.group}` : e.section.title,
      headings: [...(page.body ?? "").matchAll(/^##+ (.+)$/gm)].map((m) => m[1]),
      text: plain(toMarkdown(page, site!)),
    };
  });
  return new Response(JSON.stringify(entries), { headers: { "Content-Type": "application/json" } });
};
