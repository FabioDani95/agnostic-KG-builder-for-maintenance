// Regressions found by the independent review of 2afd41c.
import { StrictMode } from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider, useLocation } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { EditorFlow } from "../src/editor/EditorFlow";
import { LanguageProvider, setLang } from "../src/i18n/i18n";
import { document, preview, version } from "./editor-fixture";
vi.mock("../src/graph/Graph3D", () => ({ Graph3D: () => <div aria-label="Graph renderer" /> }));
const path = "/manuali/m/versioni/runs~v3_r1/modifica";
let creates = 0;
let acceptStatus = 201;
const created = {
  version: { ...version, kind: "revision", version_id: "revision~saved", status: "approved", decided_by: "human" },
  parent_version_id: version.version_id, request_id: "r", graph_hash: "h", id_map: {},
};
function Saved() {
  const location = useLocation();
  return <div>Saved graph search={location.search}</div>;
}
function boot() {
  const router = createMemoryRouter(
    [
      { path: "/manuali/:manualId/versioni/:versionId/modifica", element: <EditorFlow /> },
      { path: "/manuali/:manualId/versioni/:versionId", element: <Saved /> },
    ],
    { initialEntries: [path] },
  );
  render(<StrictMode><LanguageProvider><RouterProvider router={router} /></LanguageProvider></StrictMode>);
  return router;
}
async function toSummary() {
  const input = await screen.findByLabelText("Noise: name");
  fireEvent.focus(input);
  fireEvent.change(input, { target: { value: "Changed" } });
  fireEvent.blur(input);
  fireEvent.click(screen.getByRole("button", { name: "Avanti: controlla" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "Avanti: riepilogo" }).hasAttribute("disabled")).toBe(false));
  fireEvent.click(screen.getByRole("button", { name: "Avanti: riepilogo" }));
  await screen.findByRole("heading", { name: "Riepilogo" });
  fireEvent.click(screen.getByLabelText("Accetto la nuova versione con i dubbi residui elencati"));
}
beforeEach(() => {
  creates = 0;
  acceptStatus = 201;
  setLang("it");
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    if (url.endsWith("/editor")) return Response.json(structuredClone(document));
    if (url === "/api/manuals/m") return Response.json({ id: "m", machine: { name: "Pump" }, versions: [version] });
    if (url.endsWith("/validate-edits")) return Response.json(preview(JSON.parse(init!.body as string)));
    if (url.endsWith("/revisions")) {
      creates++;
      return acceptStatus === 201
        ? Response.json(created, { status: 201 })
        : Response.json({ detail: { code: "BASE_CHANGED" } }, { status: acceptStatus });
    }
    return Response.json({});
  });
  Element.prototype.scrollIntoView = () => undefined;
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("after acceptance the saved version opens with the confirmation flag and no editor parameters", async () => {
  const router = boot();
  await toSummary();
  fireEvent.click(screen.getByRole("button", { name: "Accetta modifiche e crea nuova versione" }));
  await screen.findByText(/Saved graph/);
  await new Promise((r) => setTimeout(r, 50));
  expect(router.state.location.pathname).toBe("/manuali/m/versioni/revision~saved");
  expect(router.state.location.search).toBe("?salvato=1");
});

it("after a 409 BASE_CHANGED the same stale preview cannot be accepted again", async () => {
  boot();
  await toSummary();
  acceptStatus = 409;
  fireEvent.click(screen.getByRole("button", { name: "Accetta modifiche e crea nuova versione" }));
  await screen.findByRole("heading", { name: "Controlla" });
  // Plan 7.3: keep the draft, show the conflict; acceptance must not stay available on the stale base.
  expect(screen.getByRole("button", { name: "Avanti: riepilogo" }).hasAttribute("disabled")).toBe(true);
});
