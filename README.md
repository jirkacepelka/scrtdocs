# Secret Network Docs

A standalone Astro site that rebuilds docs.scrt.network in scrt.network's design language: the same tokens, fonts, grain and prose styles, plus copies of its logo and badge. It is a separate project from the main site.

```bash
npm install
npm run dev     # http://localhost:4321
npm run check
npm run build
```

## What it does

- Classic docs layout: top bar with section tabs, search (Ctrl K or `/`), a full-width toggle and a link to scrt.network; a sidebar with collapsible groups and a filter (a drawer below `lg`); breadcrumbs, previous/next links and "On this page" (a jump list below `xl`).
- Page actions under every title: Copy as Markdown, View as Markdown, Download .md, MDX source, and the updated date.
- The same machine-readable files as docs.scrt.network: `…/index.md` for every page, `…/index.mdx` (the source), `/llms.txt`, `/<folder>/llms.txt` and `/llms-full.txt`.
- Code blocks have a copy button. `:::note`, `:::caution` and `:::notice` render as callouts (`src/lib/remark-callouts.mjs`).
- Footer: license and publisher as on docs.scrt.network, and the social links from scrt.network.

## Content

- Pages are the MDX sources from docs.scrt.network in `src/content/docs/` (read 2026-10-28). Do not reformat them: `src/content/` is in `.prettierignore`. The frontmatter adds `slug` (the URL; `index` is the home page), `updated` and `updatedNote`.
- MDX components the sources use live in `src/components/mdx/`: `Flowchart` (Mermaid, rendered on the client), `Tabs`/`TabItem`, `SetupNodeCurl` and `RestoreCurl`. Pass any new one in `src/pages/[...slug].astro` and teach `toMarkdown()` in `src/lib/docs.ts` how to write it as Markdown.
- The sidebar order, groups and labels are in `src/data/site.ts` (`nav`). The build fails if a page is missing from it.
- `public/secret-setup.py` and `public/restore.sh` are the scripts the Quick Setup and Sync pages tell operators to download from this host. They are copies from docs.scrt.network; keep them in sync with the source.

## Design

`src/styles/tokens.css` is a copy of the main site's file, and `src/styles/global.css` starts from it with docs additions at the end. When the main site's tokens change, copy them here too. The rules in `docs/Design System.md` and `docs/Style guardrails.md` of the main site ([jirkacepelka/scrtweb](https://github.com/jirkacepelka/scrtweb)) apply.

## Deploy

Static output with the Vercel adapter. On Vercel, create a project with `docs-site` as the root directory. Set `SITE_URL` if the domain is not docs.scrt.network.
