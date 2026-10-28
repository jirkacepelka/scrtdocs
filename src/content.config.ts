/**
 * Docs pages: the MDX sources from docs.scrt.network in src/content/docs/ (the file path is the
 * URL). Starlight's schema plus the "Updated from …" line shown under each title.
 */
import { defineCollection } from "astro:content";
import { z } from "astro/zod";
import { docsLoader } from "@astrojs/starlight/loaders";
import { docsSchema } from "@astrojs/starlight/schema";

export const collections = {
  docs: defineCollection({
    loader: docsLoader(),
    schema: docsSchema({
      extend: z.object({
        updated: z.coerce.date(),
        /** Shown before the date: "Updated from v1.27.2 notes, Oct 3, 2026". */
        updatedNote: z.string().optional(),
      }),
    }),
  }),
};
