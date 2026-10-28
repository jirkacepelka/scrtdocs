/** Documentation index for AI agents: the home page and one llms.txt per folder. */
import type { APIRoute } from "astro";
import { getPages } from "../lib/docs";

export const GET: APIRoute = async ({ site }) => {
  const pages = await getPages();
  const home = pages.get("index")!;
  const folders = [
    ...new Set(
      [...pages.keys()]
        .filter((id) => id.includes("/") || id !== "index")
        .map((id) => id.split("/")[0]),
    ),
  ];
  const url = (p: string) => new URL(p, site).href;
  const text = [
    "# Secret Network",
    "",
    "Run a Secret Network node on secret-4 with binary 1.27.2. Operator documentation from Secret³ Dev.",
    "",
    `Full documentation (discoverable current pages, one document): ${url("/llms-full.txt")}`,
    "",
    "## Pages",
    "",
    `- [${home.data.title}](${url("/index.md")}) — ${home.data.description}`,
    ...folders.map((f) => `- [${f}](${url(`/${f}/llms.txt`)})`),
    "",
  ].join("\n");
  return new Response(text, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
};
