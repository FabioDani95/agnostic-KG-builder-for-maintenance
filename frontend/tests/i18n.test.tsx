import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { GUIDE } from "../src/help/guide";
import { GUIDE_EN } from "../src/help/guide.en";
import { EN } from "../src/i18n/en";
import { setLang, tr } from "../src/i18n/i18n";
import { Library } from "../src/screens/Library";
import { statusLabel, versionLabel } from "../src/text/it";

const sources = import.meta.glob("../src/**/*.{ts,tsx}", { query: "?raw", import: "default", eager: true }) as Record<string, string>;

afterEach(() => {
  cleanup();
  setLang("it");
  vi.restoreAllMocks();
});

describe("the English interface", () => {
  it("has an English entry for every text passed to tr()", () => {
    const missing = new Set<string>();
    for (const [path, text] of Object.entries(sources)) {
      if (path.includes("/i18n/")) continue;
      for (const match of text.matchAll(/\btr\(\s*"((?:[^"\\]|\\.)*)"/g)) {
        if (!(match[1] in EN)) missing.add(`${path}: ${match[1]}`);
      }
    }
    expect([...missing]).toEqual([]);
  });

  it("fills values and reads shared labels in the chosen language", () => {
    setLang("en");
    expect(tr("Rispondi alle {n} domande", { n: 3 })).toBe("Answer the 3 questions");
    expect(statusLabel("approved", "auto")).toBe("Approved by the system");
    const copy = {
      version_id: "workspace~risposte-1", origin: "workspace", iteration: "", run: "risposte-1", repetition: null,
      copied_from: "campaign/x",
    } as unknown as Parameters<typeof versionLabel>[0];
    expect(versionLabel(copy)).toBe("Answers 1");
    setLang("it");
    expect(versionLabel(copy)).toBe("Risposte 1");
  });

  it("has the same guide chapters and sections in both languages", () => {
    const shape = (guide: typeof GUIDE) => guide.map((chapter) => [chapter.slug, chapter.sections.map((section) => section.id)]);
    expect(shape(GUIDE_EN)).toEqual(shape(GUIDE));
  });

  it("shows the library in English", async () => {
    setLang("en");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(Response.json([]));
    render(
      <MemoryRouter>
        <Library />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("No manuals yet. Upload the first with “New graph”.")).toBeTruthy());
    expect(screen.getByRole("heading", { level: 1, name: "Graphs" })).toBeTruthy();
    expect(screen.getByRole("link", { name: /New graph/ })).toBeTruthy();
  });
});
