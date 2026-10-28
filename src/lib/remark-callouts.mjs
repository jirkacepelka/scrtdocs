/**
 * Turns `:::note[Title]`, `:::caution`, `:::notice` (and tip/danger) container directives into
 * <aside class="callout callout-<type>"> with a title line. Styles live in global.css.
 */
import { visit } from "unist-util-visit";

const titles = {
  note: "Note",
  tip: "Tip",
  notice: "Notice",
  caution: "Caution",
  danger: "Danger",
};

export default function remarkCallouts() {
  return (tree) => {
    visit(tree, "containerDirective", (node) => {
      const type = node.name in titles ? node.name : "note";
      const labelIndex = node.children.findIndex((c) => c.data?.directiveLabel);
      const label = labelIndex >= 0 ? node.children.splice(labelIndex, 1)[0].children : null;
      node.children.unshift({
        type: "paragraph",
        data: { hProperties: { className: ["callout-title"] } },
        children: label ?? [{ type: "text", value: titles[type] }],
      });
      node.data = {
        hName: "aside",
        hProperties: { className: ["callout", `callout-${type}`] },
      };
    });
  };
}
