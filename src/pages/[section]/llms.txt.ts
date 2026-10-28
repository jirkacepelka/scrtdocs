/** Per-folder page list for AI agents, linking each page's Markdown export. */
import type { APIRoute, GetStaticPaths } from "astro";
import { getPages, mdUrl } from "../../lib/docs";

export const getStaticPaths = (async () => {
  const pages = await getPages();
  const folders = new Set(
    [...pages.keys()].filter((id) => id !== "index").map((id) => id.split("/")[0]),
  );
  return [...folders].map((section) => ({ params: { section } }));
}) satisfies GetStaticPaths;

export const GET: APIRoute = async ({ params, site }) => {
  const pages = [...(await getPages()).values()]
    .filter((p) => p.id.split("/")[0] === params.section)
    .sort((a, b) =>
      a.id === params.section
        ? -1
        : b.id === params.section
          ? 1
          : a.data.title.localeCompare(b.data.title),
    );
  const text = [
    `# ${params.section}`,
    "",
    "## Pages",
    "",
    ...pages.map(
      (p) =>
        `- [${p.id === params.section ? "Overview" : p.data.title}](${new URL(mdUrl(p.id), site).href}) — ${p.data.description}`,
    ),
    "",
  ].join("\n");
  return new Response(text, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
};
