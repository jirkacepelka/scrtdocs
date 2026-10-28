/** Every page as Markdown at …/index.md, in the format docs.scrt.network serves. */
import type { APIRoute, GetStaticPaths } from "astro";
import { getPages, toMarkdown, type DocPage } from "../../lib/docs";

export const getStaticPaths = (async () => {
  const pages = await getPages();
  return [...pages.values()].map((page) => ({
    params: { slug: page.id === "index" ? undefined : page.id },
    props: { page },
  }));
}) satisfies GetStaticPaths;

export const GET: APIRoute = ({ props, site }) =>
  new Response(toMarkdown((props as { page: DocPage }).page, site!), {
    headers: { "Content-Type": "text/markdown; charset=utf-8" },
  });
