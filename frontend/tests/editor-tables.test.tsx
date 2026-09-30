import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  EditorSessionProvider,
  useEditor,
} from "../src/editor/EditorSessionProvider";
import { NodeTable } from "../src/editor/NodeTable";
import { RelationTable } from "../src/editor/RelationTable";
import { EditorDetails } from "../src/editor/EditorDetails";
import { document } from "./editor-fixture";
import type { EditorDocument } from "../src/api/types";
import { setLang } from "../src/i18n/i18n";
const onGraph = vi.fn();
const onPage = vi.fn();
function Workspace() {
  const { state, dispatch, graph } = useEditor();
  return (
    <>
      <NodeTable onGraph={(id) => onGraph("node", id)} />
      <RelationTable
        onNode={(id) =>
          dispatch({ type: "select", selection: { kind: "node", id } })
        }
        onGraph={(id) => onGraph("edge", id)}
      />
      <EditorDetails
        manualId="m"
        versionId="v"
        onPage={onPage}
        onGraph={onGraph}
        onNode={(id) =>
          dispatch({ type: "select", selection: { kind: "node", id } })
        }
      />
      <button onClick={() => dispatch({ type: "undo" })}>Undo</button>
      <output data-testid="state">
        {JSON.stringify({
          graph,
          operations: state.operations,
          pending: state.pending,
          selection: state.selection,
        })}
      </output>
    </>
  );
}
function boot(value: EditorDocument = structuredClone(document)) {
  render(
    <RouterProvider
      router={createMemoryRouter([
        {
          path: "/",
          element: (
            <EditorSessionProvider document={value}>
              <Workspace />
            </EditorSessionProvider>
          ),
        },
      ])}
    />,
  );
}
function data() {
  return JSON.parse(screen.getByTestId("state").textContent!);
}
function cell(label: string, value: string, key = "Enter") {
  const input = screen.getByLabelText(label);
  fireEvent.focus(input);
  fireEvent.change(input, { target: { value } });
  fireEvent.keyDown(input, { key });
  if (key === "Tab") fireEvent.blur(input);
}
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  onGraph.mockClear();
  onPage.mockClear();
  setLang("it");
});
describe("editable tables and evidence navigation", () => {
  it("combines type, value, source and connectivity filters and supports empty types", () => {
    boot();
    fireEvent.change(screen.getByLabelText("Tipo di nodo"), {
      target: { value: "Symptom" },
    });
    fireEvent.change(screen.getByLabelText("Campo"), {
      target: { value: "count" },
    });
    fireEvent.change(screen.getByLabelText("Stato del valore"), {
      target: { value: "filled" },
    });
    fireEvent.change(screen.getAllByLabelText("Modifiche")[0], {
      target: { value: "no" },
    });
    expect(screen.getByLabelText("Noise: count")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Collegamenti"), {
      target: { value: "0" },
    });
    expect(screen.queryByLabelText("Noise: count")).toBeNull();
    expect(
      screen.getByText("Nessun risultato con questi filtri."),
    ).toBeTruthy();
  });
  it("commits typed numbers, false, empty arrays, multiline text and distinguishes null/removal", () => {
    boot();
    fireEvent.change(screen.getByLabelText("Tipo di nodo"), {
      target: { value: "Symptom" },
    });
    cell("Noise: count", "12", "Tab");
    expect(data().graph.nodes[1].properties.count).toBe(12);
    fireEvent.change(screen.getByLabelText("Noise: enabled"), {
      target: { value: "false" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Mostra campi" }));
    cell("Noise: list", '["one","two"]', "Tab");
    expect(data().graph.nodes[1].properties.list).toEqual(["one", "two"]);
    cell("Noise: list", "[]", "Tab");
    cell("Noise: description", "Line one\nLine two", "Tab");
    expect(data().graph.nodes[1].properties.description).toBe(
      "Line one\nLine two",
    );
    const count = screen.getByLabelText("Noise: count").parentElement!;
    fireEvent.click(
      within(count).getByRole("button", { name: "Imposta null" }),
    );
    expect(data().graph.nodes[1].properties.count).toBeNull();
    fireEvent.click(
      within(count).getByRole("button", { name: "Rimuovi campo facoltativo" }),
    );
    expect(data().graph.nodes[1].properties).not.toHaveProperty("count");
  });
  it("Escape cancels cell text; focusing an absent field does not create a value", () => {
    const value = structuredClone(document);
    delete value.graph.nodes[1].properties.count;
    boot(value);
    fireEvent.change(screen.getByLabelText("Tipo di nodo"), {
      target: { value: "Symptom" },
    });
    const input = screen.getByLabelText("Noise: count");
    fireEvent.focus(input);
    fireEvent.blur(input);
    expect(data().operations).toEqual([]);
    cell("Noise: name", "Discarded", "Escape");
    expect(data().graph.nodes[1].name).toBe("Noise");
    expect(data().pending).toBe(false);
  });
  it("adds isolated nodes and undo restores a deletion with its evidence and selection", () => {
    boot();
    fireEvent.click(screen.getByRole("button", { name: "Aggiungi nodo" }));
    const form = screen.getByRole("dialog", { name: "Aggiungi nodo" });
    fireEvent.change(within(form).getByLabelText("Nome"), {
      target: { value: "New symptom" },
    });
    expect(data().pending).toBe(true);
    fireEvent.submit(form);
    expect(data().graph.nodes).toHaveLength(4);
    const row = screen.getAllByLabelText("New symptom: name")[0].closest("tr")!;
    fireEvent.click(within(row).getByRole("button", { name: "Elimina" }));
    fireEvent.click(
      within(
        screen.getByRole("alertdialog", { name: "Elimina nodo" }),
      ).getByRole("button", { name: "Elimina" }),
    );
    expect(data().graph.nodes).toHaveLength(3);
    fireEvent.click(screen.getByRole("button", { name: "Undo" }));
    expect(data().graph.nodes).toHaveLength(4);
    const original = screen.getAllByLabelText("Noise: name")[0].closest("tr")!;
    fireEvent.click(
      within(original).getByRole("button", { name: "Prove (0)" }),
    );
    fireEvent.click(within(original).getByRole("button", { name: "Elimina" }));
    fireEvent.click(
      within(
        screen.getByRole("alertdialog", { name: "Elimina nodo" }),
      ).getByRole("button", { name: "Elimina" }),
    );
    expect(data().graph.edges).toHaveLength(0);
    fireEvent.click(screen.getByRole("button", { name: "Undo" }));
    expect(data().graph.edges[0].occurrences[0].evidence[0].text).toBe(
      "Noise means wear",
    );
    expect(data().selection.id).toBe("sym");
  });
  it("uses compatible endpoints and adds an occurrence for the same triple", () => {
    boot();
    fireEvent.click(screen.getByRole("button", { name: "Aggiungi relazione" }));
    const dialog = screen.getByRole("dialog", { name: "Modifica relazione" });
    const selects = within(dialog).getAllByRole("combobox");
    expect(
      within(selects[1]).queryByRole("option", { name: /Wear/ }),
    ).toBeNull();
    fireEvent.change(selects[1], { target: { value: "sym" } });
    fireEvent.change(selects[2], { target: { value: "cause" } });
    fireEvent.submit(dialog);
    expect(data().graph.edges).toHaveLength(1);
    expect(data().graph.edges[0].occurrences).toHaveLength(2);
  });
  it("navigates from relations to nodes and graph with a filter exception", () => {
    boot();
    fireEvent.change(screen.getByLabelText("Cerca nei nodi"), {
      target: { value: "unmatched" },
    });
    fireEvent.click(
      within(screen.getByRole("table", { name: "Relazioni" })).getByRole(
        "button",
        { name: "Noise" },
      ),
    );
    expect(
      screen.getByText(
        "L’elemento selezionato è mostrato anche se escluso dai filtri attivi.",
      ),
    ).toBeTruthy();
    expect(screen.getAllByLabelText("Noise: name")).toHaveLength(2);
    fireEvent.click(
      within(screen.getByRole("table", { name: "Nodi" })).getByRole("button", {
        name: "Vedi nel grafo",
      }),
    );
    expect(onGraph).toHaveBeenCalledWith("node", "sym");
  });
  it("keeps source quotes read-only and records conditions, source references and annotations", async () => {
    const value = structuredClone(document);
    value.source.segments_available = true;
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      Response.json({
        available: true,
        total: 1,
        items: [
          { segment_id: "seg", page: 1, bbox: null, text: "Noise means wear" },
        ],
      }),
    );
    boot(value);
    fireEvent.click(
      within(screen.getByRole("table", { name: "Relazioni" })).getByRole(
        "button",
        { name: "Prove (1)" },
      ),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Modifica occorrenza" }),
    );
    const form = screen.getByRole("dialog", { name: "Modifica occorrenza" });
    await waitFor(() =>
      expect(within(form).getByText(/Noise means wear/)).toBeTruthy(),
    );
    expect(
      within(form).queryByRole("textbox", { name: /Noise means wear/ }),
    ).toBeNull();
    fireEvent.click(
      within(form).getByRole("button", { name: "Aggiungi condizione" }),
    );
    fireEvent.change(within(form).getByLabelText("Testo condizione"), {
      target: { value: "Motor cold" },
    });
    fireEvent.change(within(form).getByLabelText("Annotazione personale"), {
      target: { value: "Operator note" },
    });
    fireEvent.submit(form);
    expect(data().operations.at(-1)).toMatchObject({
      op: "occurrence.update",
      segment_ids: ["seg"],
      annotation: "Operator note",
      conditions: [{ kind: "if", text: "Motor cold" }],
    });
  });
});

it("shows empty ontology types and combines filters for multiple fields", () => {
  const value = structuredClone(document);
  value.ontology.nodes.push({
    name: "Component",
    description: "",
    properties: [{ name: "name", type: "string", required: true }],
  });
  boot(value);
  fireEvent.change(screen.getByLabelText("Tipo di nodo"), {
    target: { value: "Component" },
  });
  expect(screen.getByText("Nessun risultato con questi filtri.")).toBeTruthy();
  fireEvent.change(screen.getByLabelText("Tipo di nodo"), {
    target: { value: "Symptom" },
  });
  fireEvent.change(screen.getByLabelText("Campo"), {
    target: { value: "count" },
  });
  fireEvent.change(screen.getByLabelText("Valore esatto"), {
    target: { value: "0" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Aggiungi filtro del campo" }),
  );
  fireEvent.change(screen.getByLabelText("Campo"), {
    target: { value: "enabled" },
  });
  fireEvent.change(screen.getByLabelText("Valore esatto"), {
    target: { value: "false" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Aggiungi filtro del campo" }),
  );
  expect(screen.getByLabelText("Noise: count")).toBeTruthy();
  fireEvent.change(screen.getByLabelText("Campo"), {
    target: { value: "description" },
  });
  fireEvent.change(screen.getByLabelText("Stato del valore"), {
    target: { value: "empty" },
  });
  expect(screen.queryByLabelText("Noise: count")).toBeNull();
  fireEvent.click(screen.getAllByRole("button", { name: "Rimuovi filtri" })[0]);
  expect(screen.queryByLabelText("Rimuovi filtro count")).toBeNull();
  expect(screen.getByLabelText("Noise: count")).toBeTruthy();
});

it("commits typing in the same focused cell after Escape or Enter", () => {
  boot();
  fireEvent.change(screen.getByLabelText("Tipo di nodo"),{target:{value:"Symptom"}});
  const input = screen.getByLabelText("Noise: count");
  fireEvent.focus(input);
  fireEvent.change(input,{target:{value:"invalid"}});
  fireEvent.keyDown(input,{key:"Escape"});
  fireEvent.change(input,{target:{value:"12"}});
  fireEvent.keyDown(input,{key:"Enter"});
  expect(data().graph.nodes[1].properties.count).toBe(12);
  fireEvent.change(input,{target:{value:"0"}});
  fireEvent.blur(input);
  expect(data().graph.nodes[1].properties.count).toBe(0);
});
