import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

function source(path: string): string {
  return readFileSync(resolve(process.cwd(), path), "utf8");
}

describe("review hardening", () => {
  it("defaults Button to type button while allowing an override", () => {
    const button = source("components/ui/button.tsx");

    expect(button).toContain('type = "button"');
    expect(button).toContain("type={type}");
  });

  it("protects source links opened in a new tab", () => {
    const drawer = source("components/advisor/SourceDrawer.tsx");

    expect(drawer).toContain('target="_blank" rel="noopener noreferrer"');
  });
});
