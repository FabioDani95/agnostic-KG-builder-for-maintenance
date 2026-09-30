import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  act,
} from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { LiveRun } from "../src/screens/LiveRun";
import { Library } from "../src/screens/Library";
import { FinishedGraph } from "../src/screens/FinishedGraph";
import { EditorFlow } from "../src/editor/EditorFlow";
import { document, graph, version } from "./editor-fixture";
import { LanguageProvider, setLang } from "../src/i18n/i18n";
vi.mock("../src/graph/Graph3D", () => ({
  Graph3D: () => <div aria-label="Graph renderer" />,
}));
class Source {
  static instances: Source[] = [];
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  constructor() {
    Source.instances.push(this);
  }
  close() {}
  emit(kind: string, data: object) {
    this.onmessage?.({
      data: JSON.stringify({ seq: 1, t: 0, cost_usd: 0, kind, data }),
    });
  }
}
let running = false;
beforeEach(() => {
  setLang("it");
  Source.instances = [];
  vi.stubGlobal("EventSource", Source);
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    if (url === "/api/manuals")
      return Response.json([
        {
          id: "m",
          machine: { name: "Pump", brand: "Acme", model: "M", type: "pump" },
          latest: version,
          versions: 2,
          pages: 1,
          origin: "campaign",
        },
      ]);
    if (url === "/api/manuals/m")
      return Response.json({
        id: "m",
        machine: { name: "Pump" },
        versions: [
          { ...version, status: running ? "running" : "approved" },
          { ...version, version_id: "runs~v3_r0", run: "v3_r0", repetition: 0 },
        ],
      });
    if (url.endsWith("/graph")) return Response.json(graph);
    if (url.endsWith("/editor")) {
      const value = structuredClone(document);
      if (url.includes("runs~v3_r0"))
        value.graph.nodes[1].name = value.graph.nodes[1].properties.name =
          "Historical";
      return Response.json(value);
    }
    if (url === "/api/ontology") return Response.json(document.ontology);
    return Response.json({});
  });
  Element.prototype.scrollTo = () => undefined;
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  running = false;
});
function boot(path: string) {
  const router = createMemoryRouter(
    [
      { path: "/", element: <Library /> },
      {
        path: "/manuali/:manualId/versioni/:versionId/esecuzione",
        element: <LiveRun />,
      },
      {
        path: "/manuali/:manualId/versioni/:versionId",
        element: <FinishedGraph />,
      },
      {
        path: "/manuali/:manualId/versioni/:versionId/modifica",
        element: <EditorFlow />,
      },
    ],
    { initialEntries: [path] },
  );
  render(
    <LanguageProvider>
      <RouterProvider router={router} />
    </LanguageProvider>,
  );
  return router;
}
it("FLOW-01: fake live completion redirects to its graph and dedicated editor", async () => {
  running = true;
  const router = boot("/manuali/m/versioni/runs~v3_r1/esecuzione");
  await waitFor(() => expect(Source.instances.length).toBeGreaterThan(0));
  running = false;
  await act(() =>
    Source.instances.at(-1)!.emit("run_finished", {
      status: "approved",
      verified: 1,
      doubtful: 0,
      excluded: 0,
      open_questions: 0,
    }),
  );
  const edit = await screen.findByRole("link", { name: "Modifica grafo" });
  expect(router.state.location.pathname).toBe("/manuali/m/versioni/runs~v3_r1");
  fireEvent.click(edit);
  await screen.findByLabelText("Noise: name");
  expect(router.state.location.pathname).toContain("runs~v3_r1/modifica");
});
it("FLOW-02: library, historical version and editor share the selected base", async () => {
  const router = boot("/");
  fireEvent.click(
    (await screen.findAllByRole("link", { name: /Apri il grafo/ })).find(
      (el) => el.tagName === "A",
    )!,
  );
  await screen.findByRole("link", { name: "Modifica grafo" });
  fireEvent.change(screen.getByRole("combobox", { name: "Versione" }), {
    target: { value: "runs~v3_r0" },
  });
  await waitFor(() =>
    expect(router.state.location.pathname).toContain("runs~v3_r0"),
  );
  fireEvent.click(screen.getByRole("link", { name: "Modifica grafo" }));
  await screen.findByLabelText("Historical: name");
  expect(
    (await screen.findByRole("link", { name: "Attuale v3_r0" })).getAttribute(
      "href",
    ),
  ).toContain("runs~v3_r0");
});
