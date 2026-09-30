import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import type { Preferences } from "../src/api/types";
import { SettingsDialog } from "../src/components/SettingsDialog";

const settings: Preferences = {
  reasoning: "low", reads: 2, agent_model: "gpt-6-luna", agent_reasoning: "medium", human_questions: 10,
  show_code_relations: true, node_labels: false, key: { source: "env", hint: "…vE4A" },
  choices: { reasoning: ["none", "low", "medium", "high"], agent_models: ["gpt-6-luna", "gpt-5.6-luna"] },
};

beforeAll(() => {
  HTMLDialogElement.prototype.showModal = function () {
    this.setAttribute("open", "");
  };
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("settings", () => {
  it("saves the choices, and sends a key only when one is written", async () => {
    const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(Response.json({}));
    const saved = vi.fn();
    const closed = vi.fn();
    render(<SettingsDialog settings={settings} onClose={closed} onSaved={saved} />);
    expect(screen.getByPlaceholderText("Chiave del file .env …vE4A")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "3" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Nomi sempre visibili sui nodi" }));
    fireEvent.click(screen.getByRole("button", { name: "Salva" }));
    await waitFor(() => expect(saved).toHaveBeenCalled());
    const body = JSON.parse(String(fetch.mock.calls[0][1]!.body));
    expect(body).toMatchObject({ reads: 3, node_labels: true, clear_api_key: false });
    expect(body).not.toHaveProperty("api_key");
    expect(closed).toHaveBeenCalled();
  });
});
