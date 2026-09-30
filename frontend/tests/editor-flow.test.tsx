import { StrictMode } from "react";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { createMemoryRouter, RouterProvider, Link } from "react-router-dom";
import { afterEach, beforeEach, describe, it, expect, vi } from "vitest";
import { EditorFlow } from "../src/editor/EditorFlow";
import { LanguageProvider, setLang } from "../src/i18n/i18n";
import { document, graph, preview, version } from "./editor-fixture";
import type { EditInput, AcceptRevision } from "../src/api/types";
vi.mock("../src/graph/Graph3D", () => ({
  Graph3D: () => <div aria-label="Graph renderer" />,
}));
const path = "/manuali/m/versioni/runs~v3_r1/modifica";
let creates: AcceptRevision[] = [];
let validates: EditInput[] = [];
let fail: string | null = null;
const created = {
  version: {
    ...version,
    kind: "revision",
    version_id: "revision~saved",
    status: "approved",
    decided_by: "human",
  },
  parent_version_id: version.version_id,
  request_id: "request",
  graph_hash: "hash",
  id_map: {},
};
function boot(entry = path, initialEntries = ["/", entry]) {
  const router = createMemoryRouter(
    [
      { path: "/", element: <Link to={path}>Open editor</Link> },
      {
        path: "/manuali/:manualId/versioni/:versionId/modifica",
        element: <EditorFlow />,
      },
      {
        path: "/manuali/:manualId/versioni/:versionId",
        element: (
          <div>
            Saved graph<Link to={path}>Open editor</Link>
          </div>
        ),
      },
      { path: "/tocca-a-te", element: <div>Inbox</div> },
      { path: "/manuali/:manualId", element: <div>Manual</div> },
    ],
    { initialEntries, initialIndex: initialEntries.length - 1 },
  );
  render(
    <StrictMode>
      <LanguageProvider>
        <RouterProvider router={router} />
      </LanguageProvider>
    </StrictMode>,
  );
  return router;
}
async function edit(value = "Changed") {
  const input = await screen.findByLabelText("Noise: name");
  fireEvent.focus(input);
  fireEvent.change(input, { target: { value } });
  fireEvent.blur(input);
}
async function summary() {
  fireEvent.click(screen.getByRole("button", { name: "Avanti: controlla" }));
  await waitFor(() =>
    expect(
      screen
        .getByRole("button", { name: "Avanti: riepilogo" })
        .hasAttribute("disabled"),
    ).toBe(false),
  );
  fireEvent.click(screen.getByRole("button", { name: "Avanti: riepilogo" }));
  await screen.findByRole("heading", { name: "Riepilogo" });
}
beforeEach(() => {
  creates = [];
  validates = [];
  fail = null;
  setLang("it");
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    if (url.endsWith("/editor"))
      return Response.json(structuredClone(document));
    if (url === "/api/manuals/m")
      return Response.json({
        id: "m",
        machine: { name: "Pump" },
        versions: [version],
      });
    if (url.endsWith("/validate-edits")) {
      const body = JSON.parse(init!.body as string);
      validates.push(body);
      if (fail === "409")
        return Response.json(
          { detail: { code: "BASE_CHANGED" } },
          { status: 409 },
        );
      return Response.json(preview(body));
    }
    if (url.endsWith("/revisions")) {
      creates.push(JSON.parse(init!.body as string));
      if (fail === "timeout") throw new TypeError("offline");
      return Response.json(created, { status: 201 });
    }
    if (url.includes("/revision-requests/"))
      return Response.json({ status: "saved", result: created });
    if (url.endsWith("/graph")) return Response.json(graph);
    return Response.json({});
  });
  Element.prototype.scrollIntoView = () => undefined;
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  setLang("it");
});
describe("editor flow with a real data router", () => {
  it("FLOW-03/04/14: navigation preserves input and never saves; edits expire preview and acknowledgements", async () => {
    const router = boot();
    await edit();
    await summary();
    expect(creates).toHaveLength(0);
    fireEvent.click(
      screen.getByLabelText(
        "Accetto la nuova versione con i dubbi residui elencati",
      ),
    );
    fireEvent.click(
      screen.getByRole("button", { name: /Torna a modificare · Changed/ }),
    );
    const input = screen.getAllByLabelText("Changed: name")[0];
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "Again" } });
    fireEvent.blur(input);
    await act(() => router.navigate(1));
    await waitFor(() =>
      expect(screen.queryByRole("heading", { name: "Riepilogo" })).toBeNull(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Avanti: controlla" }));
    await waitFor(() => expect(validates.at(-1)?.draft_generation).toBe(2));
    expect(creates).toHaveLength(0);
  });
  it("FLOW-05: final click sends one acceptance and opens the accepted version", async () => {
    boot();
    await edit();
    await summary();
    const accept = screen.getByRole("button", {
      name: "Accetta modifiche e crea nuova versione",
    });
    expect(accept.hasAttribute("disabled")).toBe(true);
    fireEvent.click(
      screen.getByLabelText(
        "Accetto la nuova versione con i dubbi residui elencati",
      ),
    );
    fireEvent.click(accept);
    fireEvent.click(accept);
    await screen.findByText("Saved graph");
    expect(creates).toHaveLength(1);
    expect(creates[0].acceptance.decision).toBe("accept_changes");
    expect(creates[0].preview_hash).toBe("hash_1");
  });
  it("FLOW-06/07: continue retains edits; confirmed discard destroys the session, including forward history", async () => {
    const router = boot();
    await edit();
    fireEvent.click(screen.getByRole("button", { name: "Esci senza salvare" }));
    await screen.findByRole("alertdialog");
    fireEvent.click(
      screen.getByRole("button", { name: "Continua a modificare" }),
    );
    expect(screen.getByLabelText("Changed: name")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Esci senza salvare" }));
    fireEvent.click(
      await screen.findByRole("button", { name: "Esci e scarta" }),
    );
    await screen.findByText("Saved graph");
    await act(() => router.navigate(-1));
    await screen.findByLabelText("Noise: name");
    expect(creates).toHaveLength(0);
  });
  it.each(["pop", "logo", "breadcrumb", "sidebar"])(
    "FLOW-08: %s uses the same blocker",
    async (action) => {
      const router = boot();
      await edit();
      if (action === "pop") await act(() => router.navigate(-1));
      if (action === "logo")
        fireEvent.click(screen.getByRole("link", { name: "Grafi" }));
      if (action === "breadcrumb")
        fireEvent.click(screen.getByRole("link", { name: "Pump" }));
      if (action === "sidebar")
        fireEvent.click(screen.getByRole("link", { name: "Tocca a te" }));
      await screen.findByRole("alertdialog");
      fireEvent.click(screen.getByRole("button", { name: "Esci e scarta" }));
      await waitFor(() =>
        expect(router.state.location.pathname).not.toBe(path),
      );
      expect(creates).toHaveLength(0);
    },
  );
  it("FLOW-09/13: direct summary URLs and persisted page lifecycle start from the saved base", async () => {
    boot(path + "?passo=riepilogo");
    await screen.findByLabelText("Noise: name");
    expect(
      screen.getByRole("button", { name: "Avanti: controlla" }),
    ).toBeTruthy();
    await edit();
    const event = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
    await act(() => {
      window.dispatchEvent(new Event("pagehide"));
      window.dispatchEvent(
        new PageTransitionEvent("pageshow", { persisted: true }),
      );
    });
    await screen.findByLabelText("Noise: name");
    expect(creates).toHaveLength(0);
  });
  it("FLOW-10: invalid numeric input blocks progression but warns on exit", async () => {
    boot();
    await screen.findByLabelText("Noise: name");
    fireEvent.change(screen.getByLabelText("Tipo di nodo"), {
      target: { value: "Symptom" },
    });
    const input = screen.getByLabelText("Noise: count");
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "oops" } });
    fireEvent.blur(input);
    fireEvent.click(screen.getByRole("button", { name: "Avanti: controlla" }));
    expect(screen.getByRole("alert").textContent).toContain("numero valido");
    expect(validates).toHaveLength(0);
    fireEvent.click(screen.getByRole("button", { name: "Esci senza salvare" }));
    await screen.findByRole("alertdialog");
    expect(creates).toHaveLength(0);
  });
  it("FLOW-11: full undo disables acceptance", async () => {
    boot();
    await edit();
    fireEvent.click(screen.getByRole("button", { name: "Annulla modifica" }));
    await summary();
    expect(
      screen
        .getByRole("button", {
          name: "Accetta modifiche e crea nuova versione",
        })
        .hasAttribute("disabled"),
    ).toBe(true);
    expect(creates).toHaveLength(0);
  });
  it("FLOW-12: an ambiguous response resolves the same request and preserves the frozen payload", async () => {
    boot();
    await edit();
    await summary();
    fireEvent.click(
      screen.getByLabelText(
        "Accetto la nuova versione con i dubbi residui elencati",
      ),
    );
    fail = "timeout";
    fireEvent.click(
      screen.getByRole("button", {
        name: "Accetta modifiche e crea nuova versione",
      }),
    );
    await screen.findByText(
      "L’esito della richiesta è incerto. Verifica la stessa richiesta prima di continuare.",
    );
    expect(
      screen.queryByRole("button", { name: "Esci senza salvare" }),
    ).toBeNull();
    fireEvent.click(
      screen.getAllByRole("button", { name: "Verifica il salvataggio" })[0],
    );
    await screen.findByText("Saved graph");
    expect(creates).toHaveLength(1);
  });
});

it.each([409, 422])(
  "FLOW-12: %s on acceptance keeps the draft and returns to checks",
  async (status) => {
    boot();
    await edit();
    await summary();
    fireEvent.click(
      screen.getByLabelText(
        "Accetto la nuova versione con i dubbi residui elencati",
      ),
    );
    const normal = vi.mocked(globalThis.fetch).getMockImplementation()!;
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) =>
      String(input).endsWith("/revisions")
        ? Response.json(
            {
              detail: {
                code: status === 409 ? "STALE_PREVIEW" : "VALIDATION_FAILED",
              },
            },
            { status },
          )
        : normal(input, init),
    );
    fireEvent.click(
      screen.getByRole("button", {
        name: "Accetta modifiche e crea nuova versione",
      }),
    );
    await screen.findByRole("heading", { name: "Controlla" });
    fireEvent.click(screen.getByRole("button", { name: "Indietro" }));
    await screen.findByLabelText("Changed: name");
  },
);

it("FLOW-12: a stale response cannot enable acceptance after a correction", async () => {
  boot();
  await edit();
  const normal = vi.mocked(globalThis.fetch).getMockImplementation()!;
  let deliver: (value: Response) => void = () => undefined;
  let first = true;
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    if (String(input).endsWith("/validate-edits") && first) {
      first = false;
      const body = JSON.parse(init!.body as string);
      validates.push(body);
      return new Promise<Response>((resolve) => {
        deliver = resolve;
      });
    }
    return normal(input, init);
  });
  fireEvent.click(screen.getByRole("button", { name: "Avanti: controlla" }));
  await waitFor(() => expect(validates).toHaveLength(1));
  fireEvent.click(screen.getByRole("button", { name: "Indietro" }));
  const input = screen.getByLabelText("Changed: name");
  fireEvent.focus(input);
  fireEvent.change(input, { target: { value: "New generation" } });
  fireEvent.blur(input);
  await act(() => deliver(Response.json(preview(validates[0]))));
  fireEvent.click(screen.getByRole("button", { name: "Avanti: controlla" }));
  await waitFor(() => expect(validates.at(-1)?.draft_generation).toBe(2));
  expect(creates).toHaveLength(0);
});

it("FLOW-08: another version applies the blocker and loads the correct base", async () => {
  const router = boot();
  await edit();
  const normal = vi.mocked(globalThis.fetch).getMockImplementation()!;
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    if (String(input).includes("versioni/")) return normal(input, init);
    if (String(input).includes("runs~v3_r2/editor")) {
      const other = structuredClone(document);
      other.graph.nodes[1].name = other.graph.nodes[1].properties.name =
        "Other version";
      return Response.json(other);
    }
    return normal(input, init);
  });
  await act(() => router.navigate("/manuali/m/versioni/runs~v3_r2/modifica"));
  await screen.findByRole("alertdialog");
  fireEvent.click(screen.getByRole("button", { name: "Esci e scarta" }));
  await screen.findByLabelText("Other version: name");
  expect(screen.queryByLabelText("Changed: name")).toBeNull();
  expect(creates).toHaveLength(0);
});

it("FLOW-09: page lifecycle clears summary URL, preview and acknowledgements", async () => {
  const router = boot();
  await edit();
  await summary();
  fireEvent.click(
    screen.getByLabelText(
      "Accetto la nuova versione con i dubbi residui elencati",
    ),
  );
  await act(() => {
    window.dispatchEvent(new Event("pagehide"));
    window.dispatchEvent(
      new PageTransitionEvent("pageshow", { persisted: true }),
    );
  });
  await screen.findByRole("button", { name: "Avanti: controlla" });
  expect(router.state.location.search).toContain("passo=modifica");
  expect(screen.getByLabelText("Noise: name")).toBeTruthy();
  expect(creates).toHaveLength(0);
});

it("language switching preserves values, undo and the same memory session", async () => {
  boot();
  await edit();
  fireEvent.click(screen.getByRole("button", { name: "Switch to English" }));
  await screen.findByRole("button", { name: "Next: check" });
  expect(screen.getByLabelText("Changed: name")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Undo change" }));
  await screen.findByLabelText("Noise: name");
});
