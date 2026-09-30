import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Shell } from "../src/components/Shell";
import { StatusProvider } from "../src/status/StatusProvider";

const answers: Record<string, unknown> = {
  "/api/manuals": [
    {
      id: "m1",
      origin: "workspace",
      machine: { name: "M1 pump", brand: "Acme", model: "M1", type: "pump" },
      pages: 18,
      versions: 2,
      latest: { version_id: "workspace~v3_r1", status: "awaiting_approval", open_questions: 3 },
    },
  ],
  "/api/jobs/active": { run: "m1/runs/v3_r2" },
};

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("the frame", () => {
  it("shows what waits for a person, and the run in progress, on any screen", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) =>
      Response.json(answers[String(input)] ?? {}),
    );
    render(
      <MemoryRouter>
        <StatusProvider>
          <Shell trail={[{ to: "/", label: "Grafi" }]} title="M1 pump" />
        </StatusProvider>
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByRole("link", { name: "Tocca a te, 1 in attesa" })).toBeTruthy());
    const live = screen.getByRole("link", { name: "Esecuzione in corso: Acme M1" });
    expect(live.getAttribute("href")).toBe("/manuali/m1/versioni/workspace~v3_r2/esecuzione");
    expect(screen.queryByText(/Spesa/)).toBeNull();
    expect(screen.getByRole("heading", { level: 1, name: "M1 pump" })).toBeTruthy();
    expect(document.title).toBe("M1 pump · Grafi di manutenzione");
  });
});
