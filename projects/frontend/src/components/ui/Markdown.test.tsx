import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Markdown } from "@/components/ui/Markdown";

describe("Markdown", () => {
  it("renders bold, headings, and lists instead of raw markdown source", () => {
    render(
      <Markdown>{"## Summary\n\nThe fund is **diversified**.\n\n- low TER\n- global"}</Markdown>
    );

    // heading rendered as a real heading element, not literal "## Summary"
    expect(screen.getByRole("heading", { name: "Summary" })).toBeTruthy();
    // emphasis rendered as <strong>, not literal "**diversified**"
    expect(screen.getByText("diversified").tagName).toBe("STRONG");
    // bullet list rendered as list items
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    // no raw markdown markers leak into the text
    expect(screen.queryByText(/\*\*/)).toBeNull();
  });

  it("renders GFM tables", () => {
    render(<Markdown>{"| Metric | Value |\n| --- | --- |\n| TER | 0.20% |"}</Markdown>);

    expect(screen.getByRole("table")).toBeTruthy();
    expect(screen.getByRole("columnheader", { name: "Metric" })).toBeTruthy();
    expect(screen.getByRole("cell", { name: "0.20%" })).toBeTruthy();
  });
});
