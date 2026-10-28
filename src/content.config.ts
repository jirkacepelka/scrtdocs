/**
 * Docs pages: the MDX sources from docs.scrt.network, one file per page in src/content/docs/.
 * The frontmatter `slug` is the URL path ("index" is the home page). Navigation order and
 * groups live in src/data/site.ts.
 */
import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";

const docs = defineCollection({
  loader: glob({ pattern: "**/*.mdx", base: "./src/content/docs" }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    updated: z.coerce.date(),
    /** Shown before the date: "Updated from v1.27.2 notes, Oct 3, 2026". */
    updatedNote: z.string().optional(),
  }),
});

export const collections = { docs };
