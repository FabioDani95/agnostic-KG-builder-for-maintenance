import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ManualRow } from "../src/api/types";
import { Library, matches, needsReview } from "../src/screens/Library";

const row = (id: string, status: "approved" | "awaiting_approval", open: number): ManualRow => ({
  id,
  origin: "campaign",
  machine: { name: `${id} machine`, brand: "Acme", model: id.toUpperCase(), type: "pump" },
  pages: 18,
  versions: 1,
  latest: {
    version_id: "runs~v3_r1", origin: "campaign", iteration: "", run: "v3_r1", repetition: 1, date: null,
    commit: "abc1234", verified: 62, doubtful: 0, excluded: 1, open_questions: open, status, decided_by: "auto",
    cost_usd: 0.02, seconds: 100, pages: 18, replay: true, copied_from: null,
  },
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("library", () => {
  it("filters by text and by what needs a review", () => {
    expect(matches(row("p1", "approved", 0), "acme")).toBe(true);
    expect(matches(row("p1", "approved", 0), "valve")).toBe(false);
    expect(needsReview(row("p1", "approved", 2))).toBe(true);
    expect(needsReview(row("p1", "awaiting_approval", 0))).toBe(true);
    expect(needsReview(row("p1", "approved", 0))).toBe(false);
  });

  it("shows one row per manual with real numbers", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify([row("p1", "approved", 0), row("p2", "awaiting_approval", 3)])),
    );
    render(
      <MemoryRouter>
        <Library />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getAllByRole("link", { name: /Acme/ })).toHaveLength(2));
    expect(screen.getByText("Acme P2")).toBeTruthy();
    expect(screen.getByText("Da approvare")).toBeTruthy();
    expect(screen.getByText("Approvato in automatico")).toBeTruthy();
  });
});
