import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import { GUIDE } from "../src/help/guide";
import { Guide } from "../src/screens/Guide";

beforeAll(() => {
  globalThis.IntersectionObserver = class {
    observe() {}
    disconnect() {}
  } as unknown as typeof IntersectionObserver;
  Element.prototype.scrollTo = () => undefined;
});

afterEach(cleanup);

const open = (path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/guida" element={<Guide />} />
        <Route path="/guida/:chapter" element={<Guide />} />
      </Routes>
    </MemoryRouter>,
  );

describe("the guide", () => {
  it("shows a chapter with its sections and the way to the next one", () => {
    open("/guida/estrazione");
    expect(screen.getByRole("heading", { level: 2, name: "Come lavora l'estrazione" })).toBeTruthy();
    for (const station of ["Leggi", "Mappa", "Estrai", "Controlla", "Unisci", "Chiedi"]) {
      expect(screen.getByRole("heading", { level: 3, name: station })).toBeTruthy();
    }
    expect(screen.getByRole("link", { name: /Successivo\s*Domande e approvazione/ })).toBeTruthy();
  });

  it("opens the first chapter for an unknown address", () => {
    open("/guida/non-esiste");
    expect(screen.getByRole("heading", { level: 2, name: GUIDE[0].title })).toBeTruthy();
  });

  it("speaks to people, not developers: no code in the text", () => {
    const text = JSON.stringify(GUIDE);
    expect(text).not.toMatch(/`|\.py\b|\.json\b|\/api\/|--[a-z]/);
  });
});
