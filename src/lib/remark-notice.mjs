/**
 * docs.scrt.network uses `:::notice`, which Starlight's asides don't know. Render it as a note
 * titled "Notice" (unless it has its own [label]).
 */
import { visit } from "unist-util-visit";

export default function remarkNotice() {
  return (tree) => {
    visit(tree, "containerDirective", (node) => {
      if (node.name !== "notice") return;
      node.name = "note";
      if (!node.children.some((c) => c.data?.directiveLabel)) {
        node.children.unshift({
          type: "paragraph",
          data: { directiveLabel: true },
          children: [{ type: "text", value: "Notice" }],
        });
      }
    });
  };
}
