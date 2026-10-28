/** All pages as Markdown in one document, in sidebar order. */
import type { APIRoute } from "astro";
import { flatNav, getPages, toMarkdown } from "../lib/docs";

export const GET: APIRoute = async ({ site }) => {
  const pages = await getPages();
  const text = flatNav(pages)
    .map((e) => toMarkdown(pages.get(e.slug)!, site!))
    .join("\n\n");
  return new Response(text, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
};
