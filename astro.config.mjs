// @ts-check
import { defineConfig } from "astro/config";
import vercel from "@astrojs/vercel";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import icon from "astro-icon";
import tailwindcss from "@tailwindcss/vite";
import remarkDirective from "remark-directive";
import remarkCallouts from "./src/lib/remark-callouts.mjs";

// Canonical URL for sitemap, OG tags and the Markdown/llms.txt links. Override with SITE_URL.
const site = process.env.SITE_URL ?? "https://docs.scrt.network";

export default defineConfig({
  site,
  output: "static",
  adapter: vercel({ webAnalytics: { enabled: false } }),
  integrations: [mdx(), sitemap(), icon()],
  vite: {
    plugins: [tailwindcss()],
  },
  markdown: {
    remarkPlugins: [remarkDirective, remarkCallouts],
    shikiConfig: { theme: "github-dark-default" },
  },
});
