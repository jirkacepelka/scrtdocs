// @ts-check
import { defineConfig } from "astro/config";
import vercel from "@astrojs/vercel";
import starlight from "@astrojs/starlight";
import AutoImport from "astro-auto-import";
import remarkNotice from "./src/lib/remark-notice.mjs";
import { site, sidebar, social } from "./src/data/site.mjs";

// The MDX sources from docs.scrt.network use these components without importing them.
const mdxComponents = [
  { "@astrojs/starlight/components": ["Tabs", "TabItem"] },
  "./src/components/mdx/Flowchart.astro",
  "./src/components/mdx/SetupNodeCurl.astro",
  "./src/components/mdx/RestoreCurl.astro",
];

export default defineConfig({
  site: site.url,
  output: "static",
  adapter: vercel({ webAnalytics: { enabled: false } }),
  markdown: {
    remarkPlugins: [remarkNotice],
  },
  integrations: [
    starlight({
      title: site.title,
      description: site.description,
      logo: {
        dark: "./src/assets/logo-dark.svg",
        light: "./src/assets/logo-light.svg",
        alt: "Secret Network",
      },
      favicon: "/favicon.svg",
      social,
      sidebar,
      customCss: [
        "@fontsource-variable/geist",
        "@fontsource-variable/geist-mono",
        "./src/styles/theme.css",
      ],
      expressiveCode: {
        themes: ["github-dark-default", "github-light-default"],
        styleOverrides: {
          borderRadius: "0.875rem",
          borderColor: "var(--sl-color-hairline)",
          codeFontFamily: "var(--sl-font-mono)",
          uiFontFamily: "var(--sl-font)",
          frames: { shadowColor: "transparent" },
        },
      },
      head: [
        {
          tag: "script",
          content:
            "try{localStorage.getItem('docs:wide')&&document.documentElement.setAttribute('data-wide','')}catch{}",
        },
        { tag: "link", attrs: { rel: "help", type: "text/plain", href: "/llms.txt" } },
      ],
      components: {
        Head: "./src/components/overrides/Head.astro",
        SiteTitle: "./src/components/overrides/SiteTitle.astro",
        ThemeSelect: "./src/components/overrides/ThemeSelect.astro",
        PageTitle: "./src/components/overrides/PageTitle.astro",
        Footer: "./src/components/overrides/Footer.astro",
      },
    }),
    // After Starlight, so the MDX integration it adds is already registered.
    AutoImport({ imports: mdxComponents }),
  ],
});
