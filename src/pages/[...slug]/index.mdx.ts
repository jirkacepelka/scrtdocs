/** Every page's MDX source at …/index.mdx. */
import type { APIRoute, GetStaticPaths } from "astro";
import { getPages, toMdx, type DocPage } from "../../lib/docs";

export const getStaticPaths = (async () => {
  const pages = await getPages();
  return [...pages.values()].map((page) => ({
    params: { slug: page.id === "index" ? undefined : page.id },
    props: { page },
  }));
}) satisfies GetStaticPaths;

export const GET: APIRoute = ({ props }) =>
  new Response(toMdx((props as { page: DocPage }).page), {
    headers: { "Content-Type": "text/markdown; charset=utf-8" },
  });
