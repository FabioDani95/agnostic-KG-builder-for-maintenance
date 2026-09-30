// Shared table and evidence workspace. Loading belongs to the enclosing version screen.
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import type {
  Evidence,
  Graph,
  Ontology,
  EditorDocument,
  EditPreview,
  Issue,
} from "../api/types";
import {
  EditorSessionProvider,
  useEditor,
} from "../editor/EditorSessionProvider";
import { NodeTable } from "../editor/NodeTable";
import { RelationTable } from "../editor/RelationTable";
import { EditorDetails } from "../editor/EditorDetails";
import { getJson, postJson, versionPath } from "../api/client";
import { ReviewPanel } from "../editor/ReviewPanel";
import { tr, useLang } from "../i18n/i18n";
export function GraphWorkspace({
  selection,
  graph,
  ontology,
  manualId,
  versionId,
  onPage,
  onGraph,
  tab,
}: {
  selection: import("../editor/reducer").Selection;
  graph: Graph;
  ontology: Ontology;
  manualId: string;
  versionId: string;
  onPage: (page: number, evidence: Evidence[]) => void;
  onGraph: (kind: "node" | "edge", id: string) => void;
  tab: string;
}) {
  const document = useMemo(
    () => ({
      graph,
      ontology,
      preconditions: {
        base_hash: "",
        ontology_hash: "",
        source_token: "",
        source_review_hash: "",
      },
      capabilities: { can_edit: false, edit_reason: null },
      source: { pdf_available: true, segments_available: false },
      source_review: { version_id: versionId },
    }),
    [graph, ontology, versionId],
  );
  return (
    <EditorSessionProvider key={versionId} document={document}>
      <Tables
        selection={selection}
        manualId={manualId}
        versionId={versionId}
        onPage={onPage}
        onGraph={onGraph}
        tab={tab}
      />
    </EditorSessionProvider>
  );
}
function Tables({
  selection,
  manualId,
  versionId,
  onPage,
  onGraph,
  tab,
}: Omit<Parameters<typeof GraphWorkspace>[0], "graph" | "ontology">) {
  useLang();
  const { dispatch, state } = useEditor();
  const [preview, setPreview] = useState<EditPreview | null>(null);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState("");
  const check = async () => {
    setChecking(true);
    setError("");
    try {
      const endpoint = versionPath(manualId, versionId);
      const context = await getJson<EditorDocument>(endpoint + "/editor");
      const next = await postJson<EditPreview>(endpoint + "/validate-edits", {
        preconditions: context.preconditions,
        operations: [],
        draft_generation: 0,
      });
      setPreview(next);
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setChecking(false);
    }
  };
  useEffect(() => {
    if (tab === "controlli" && !preview && !checking && !error) void check();
  }, [tab, preview, checking, error]);
  const target = (issue: Issue) => {
    if (!issue.target.id || issue.target.kind === "graph") return;
    const kind = issue.target.kind === "node" ? "node" : "edge";
    dispatch({
      type: "select",
      selection: { kind, id: issue.target.id, field: issue.target.field },
    });
    const next = new URLSearchParams(params);
    next.set("vista", kind === "node" ? "nodi" : "relazioni");
    setParams(next);
  };
  const [params, setParams] = useSearchParams();
  useEffect(() => {
    dispatch({ type: "select", selection });
  }, [selection, dispatch]);
  const node = (id: string) => {
    dispatch({ type: "select", selection: { kind: "node", id } });
    const next = new URLSearchParams(params);
    next.set("vista", "nodi");
    setParams(next);
  };
  return (
    <div className="editor-content editor-consult">
      <div className="editor-main">
        <div hidden={tab !== "controlli"}>
          {error && <p className="message">{error}</p>}
          <ReviewPanel
            preview={preview}
            ontology={state.document.ontology}
            onTarget={target}
            onRetry={() => void check()}
            checking={checking}
          />
          <p>{tr("Per correggere il contenuto, apri Modifica grafo.")}</p>
        </div>
        <div hidden={tab !== "nodi"}>
          <NodeTable readOnly onGraph={(id) => onGraph("node", id)} />
        </div>
        <div hidden={tab !== "relazioni"}>
          <RelationTable
            readOnly
            onNode={node}
            onGraph={(id) => onGraph("edge", id)}
          />
        </div>
      </div>
      <EditorDetails
        readOnly
        manualId={manualId}
        versionId={versionId}
        onPage={onPage}
        onNode={node}
        onGraph={onGraph}
      />
    </div>
  );
}
