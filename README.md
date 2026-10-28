# Secret Network Docs

docs.scrt.network rebuilt on [Starlight](https://starlight.astro.build) (Astro's docs framework) in scrt.network's design language: Geist, the brand orange, near-black surfaces and pills for controls, in a dark and a light theme.

```bash
npm install
npm run dev     # http://localhost:4321
npm run check
npm run build
```

## What it does

- Starlight gives the layout, sidebar, "On this page", mobile menu, previous/next links, dark/light/auto theme, code blocks with copy buttons, asides, tabs and full-text search (Pagefind, Ctrl K).
- Added on top (`src/components/overrides/`):
  - header: section tabs next to the logo (`SiteTitle`) and a full-width toggle next to the theme select (`ThemeSelect`);
  - under every title: breadcrumbs, the page description, Copy as Markdown, View as Markdown, Download .md, MDX source and the updated date (`PageTitle`);
  - footer: license and publisher as on docs.scrt.network, and the social links (`Footer`);
  - a `<link rel="alternate" type="text/markdown">` to each page's Markdown (`Head`).
- The same machine-readable files as docs.scrt.network (`src/pages/`): `…/index.md` for every page, `…/index.mdx` (the source), `/llms.txt`, `/<folder>/llms.txt` and `/llms-full.txt`.

## Content

- Pages are the MDX sources from docs.scrt.network in `src/content/docs/` (read 2026-10-28); the file path is the URL. Do not reformat them: `src/content/` is in `.prettierignore`. The frontmatter adds `updated` and `updatedNote` (the "Updated from … notes" line), and `slug` on the two upgrade pages so their URLs keep the dots (`/operators/upgrade/v1.27.3`).
- The sources use components without importing them; `astro-auto-import` provides them (`astro.config.mjs`): Starlight's `Tabs`/`TabItem`, and `Flowchart` (Mermaid, rendered on the client in the current theme), `SetupNodeCurl` and `RestoreCurl` from `src/components/mdx/`. For a new one, add it there and teach `toMarkdown()` in `src/lib/docs.ts` how to write it as Markdown.
- `:::notice` is not a Starlight aside; `src/lib/remark-notice.mjs` renders it as a note titled "Notice".
- Sidebar order, groups and labels, section tabs, social links and the license are in `src/data/site.mjs`.
- `public/secret-setup.py` and `public/restore.sh` are the scripts the Quick Setup and Sync pages tell operators to download from this host. They are copies from docs.scrt.network; keep them in sync with the source.

## Design

`src/styles/theme.css` maps Starlight's colour and font variables to scrt.network's tokens (dark) and a matching light palette. The rules in `docs/Design System.md` and `docs/Style guardrails.md` of the main site ([jirkacepelka/scrtweb](https://github.com/jirkacepelka/scrtweb)) apply.

## Deploy

Static output with the Vercel adapter. On Vercel, import this repository as a new project. Set `SITE_URL` if the domain is not docs.scrt.network.
