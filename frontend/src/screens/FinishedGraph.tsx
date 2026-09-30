import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { manualRoute, postJson, useApi, versionPath } from "../api/client";
import type { Evidence, Graph, GraphEdge, GraphNode, Manual, Questions } from "../api/types";
import { SearchField, SegmentedControl, StatusBadge, typing } from "../components/Controls";
import { EdgeDetail, NodeDetail } from "../components/EvidencePanel";
import { Icon } from "../components/Icon";
import { Legend } from "../components/Legend";
import { PageDialog } from "../components/PageDialog";
import { Shell } from "../components/Shell";
import { Graph3D, type GraphHandle, type ViewLink, type ViewNode } from "../graph/Graph3D";
import { formatNumber, TYPE_LABEL, versionLabel } from "../text/it";

type TierFilter = "all" | "green" | "yellow";
type Selection = { kind: "node" | "edge"; id: string } | null;

// Diagnostic direction: symptom or code, then causes, then actions and components.
const PATH_RELATIONS = new Set(["MAY_INDICATE", "INDICATES", "RESOLVED_BY", "AFFECTS"]);

export function diagnosticPath(root: string, edges: GraphEdge[]): Set<string> {
  const seen = new Set([root]);
  let frontier = [root];
  for (let depth = 0; depth < 3 && frontier.length; depth += 1) {
    const next: string[] = [];
    for (const edge of edges) {
      if (!edge.derived && PATH_RELATIONS.has(edge.type) && frontier.includes(edge.from) && !seen.has(edge.to)) {
        seen.add(edge.to);
        next.push(edge.to);
      }
    }
    frontier = next;
  }
  return seen;
}

export function searchStarts(nodes: GraphNode[], query: string): GraphNode[] {
  const text = query.trim().toLowerCase();
  if (!text) return [];
  return nodes
    .filter((node) => node.type === "Symptom" || node.type === "ErrorCode")
    .filter((node) =>
      [node.name, String(node.properties.code ?? ""), ...(node.aliases ?? [])].some((value) =>
        value.toLowerCase().includes(text),
      ),
    )
    .slice(0, 12);
}

export function FinishedGraph() {
  const { manualId = "", versionId = "" } = useParams();
  const navigate = useNavigate();
  const graph = useApi<Graph>(`${versionPath(manualId, versionId)}/graph`);
  const manual = useApi<Manual>(`/api/manuals/${encodeURIComponent(manualId)}`);
  const view = useRef<GraphHandle>(null);
  const [filter, setFilter] = useState<TierFilter>("all");
  const [query, setQuery] = useState("");
  const [root, setRoot] = useState<string | null>(null);
  const [selection, setSelection] = useState<Selection>(null);
  const [page, setPage] = useState<{ page: number; evidence: Evidence[] } | null>(null);
  const evidencePanel = useRef<HTMLElement>(null);
  useEffect(() => {
    evidencePanel.current?.scrollTo({ top: 0 });
  }, [selection]);
  // Esc closes the evidence, unless a page of the manual is open on top.
  useEffect(() => {
    const press = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !typing(event.target) && !document.querySelector("dialog[open]")) setSelection(null);
    };
    window.addEventListener("keydown", press);
    return () => window.removeEventListener("keydown", press);
  }, []);

  const nodes = useMemo(() => new Map((graph.data?.nodes ?? []).map((node) => [node.id, node])), [graph.data]);
  const edges = graph.data?.edges ?? [];
  const visible = useMemo(() => {
    const links = (graph.data?.edges ?? []).filter((edge) =>
      filter === "all" ? true : filter === "green" ? edge.tier === "green" : edge.tier === "yellow" && !edge.derived,
    );
    const used = new Set(links.flatMap((edge) => [edge.from, edge.to]));
    const shownNodes: ViewNode[] = (graph.data?.nodes ?? [])
      .filter((node) => used.has(node.id) || node.type === "Asset")
      .map((node) => ({ id: node.id, type: node.type, name: node.name }));
    const shownLinks: ViewLink[] = links.map((edge) => ({
      id: edge.id,
      type: edge.type,
      from: edge.from,
      to: edge.to,
      tier: edge.tier,
      derived: edge.derived,
    }));
    return { nodes: shownNodes, links: shownLinks };
  }, [graph.data, filter]);
  const focus = useMemo(() => (root ? diagnosticPath(root, edges) : null), [root, edges]);
  const counts = useMemo(() => {
    const byType: Record<string, number> = {};
    for (const node of graph.data?.nodes ?? []) byType[node.type] = (byType[node.type] ?? 0) + 1;
    return byType;
  }, [graph.data]);
  const knowledge = edges.filter((edge) => !edge.derived);
  const results = searchStarts(graph.data?.nodes ?? [], query);
  const versions = (manual.data?.versions ?? []).filter((item) => item.status !== "failed" && item.status !== "running");
  const current = manual.data?.versions.find((item) => item.version_id === versionId);
  const waiting = current?.status === "awaiting_approval" && current.origin === "workspace";
  const questions = useApi<Questions>(waiting ? `${versionPath(manualId, versionId)}/questions` : null);
  const [approving, setApproving] = useState(false);
  const approve = async () => {
    setApproving(true);
    try {
      await postJson(`${versionPath(manualId, versionId)}/approve`, { decision: "approve" });
      navigate(`/manuali/${encodeURIComponent(manualId)}/versioni/${encodeURIComponent(versionId)}/esecuzione`);
    } finally {
      setApproving(false);
    }
  };
  const open = questions.data ? questions.data.open.length : 0;

  const selectedEdge = selection?.kind === "edge" ? edges.find((edge) => edge.id === selection.id) : undefined;
  const selectedNode = selection?.kind === "node" ? nodes.get(selection.id) : undefined;
  const openPage = (number: number, evidence: Evidence[]) => setPage({ page: number, evidence });

  return (
    <Shell
      workspace
      trail={[
        { to: "/", label: "Grafi" },
        { to: manualRoute(manualId), label: manual.data?.machine.name ?? "Manuale" },
      ]}
      title={current ? versionLabel(current) : "Grafo"}
      actions={
        <>
          <div className="search-wrap">
            <SearchField label="Cerca un sintomo o un codice" value={query} onChange={setQuery} width="100%" hotkey />
            {results.length > 0 && (
              <div className="search-results" role="listbox" aria-label="Sintomi e codici trovati">
                {results.map((node) => (
                  <button
                    key={node.id}
                    type="button"
                    role="option"
                    aria-selected={root === node.id}
                    onClick={() => {
                      setRoot(node.id);
                      setSelection({ kind: "node", id: node.id });
                      setQuery("");
                    }}
                  >
                    <span style={{ display: "block" }}>{node.name}</span>
                    <span className="t-small secondary">{TYPE_LABEL[node.type]}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          {versions.length > 0 && (
            <label className="row">
              <span className="visually-hidden">Versione</span>
              <select
                className="input"
                style={{ width: 176 }}
                value={versionId}
                onChange={(event) =>
                  navigate(`/manuali/${encodeURIComponent(manualId)}/versioni/${encodeURIComponent(event.target.value)}`)
                }
              >
                {versions.map((item) => (
                  <option key={item.version_id} value={item.version_id}>
                    {versionLabel(item)}
                  </option>
                ))}
              </select>
            </label>
          )}
          {questions.data && !questions.data.can_approve && (open > 0 || questions.data.unapplied > 0) && (
            <Link
              to={`/manuali/${encodeURIComponent(manualId)}/versioni/${encodeURIComponent(versionId)}/domande`}
              className="button button-bar"
            >
              <Icon name="question" />
              {open > 0 ? (open === 1 ? "Rispondi alla domanda" : `Rispondi alle ${formatNumber(open)} domande`) : "Applica le risposte"}
            </Link>
          )}
          {questions.data?.can_approve && (
            <button type="button" className="button button-primary" disabled={approving} onClick={approve}>
              <Icon name="check" />
              Approva
            </button>
          )}
        </>
      }
    >
      <div className="workspace">
        <aside className="dock dock-left" aria-label="Filtri e legenda">
          <section className="panel-section">
            <h2 className="panel-title">Relazioni</h2>
            <SegmentedControl<TierFilter>
              label="Quali relazioni mostrare"
              fill
              value={filter}
              onChange={setFilter}
              options={[
                { value: "all", label: "Tutte" },
                { value: "green", label: "Verificate" },
                { value: "yellow", label: "In dubbio" },
              ]}
            />
          </section>
          {root && (
            <section className="panel-section">
              <h2 className="panel-title">Percorso</h2>
              <p>{nodes.get(root)?.name}</p>
              <button type="button" className="button button-plain" style={{ paddingLeft: 0 }} onClick={() => setRoot(null)}>
                Mostra tutto il grafo
              </button>
            </section>
          )}
          <section className="panel-section">
            <h2 className="panel-title">Legenda</h2>
            <Legend counts={counts} />
          </section>
          <section className="panel-section">
            <h2 className="panel-title">Versione</h2>
            {current && (
              <dl className="data-list" style={{ gridTemplateColumns: "56px 1fr", alignItems: "center" }}>
                <dt>Esito</dt>
                <dd>
                  <StatusBadge status={current.status} decidedBy={current.decided_by} />
                </dd>
                <dt>Codice</dt>
                <dd className="mono">{current.commit}</dd>
              </dl>
            )}
          </section>
          <section className="panel-section">
            <h2 className="panel-title">Vista</h2>
            <div className="row">
              <button type="button" className="button button-secondary" onClick={() => view.current?.relayout()}>
                <Icon name="relayout" />
                Riordina
              </button>
              <button type="button" className="button button-secondary" onClick={() => view.current?.fit()}>
                <Icon name="frame" />
                Inquadra
              </button>
            </div>
          </section>
        </aside>

        <div className="canvas">
          {graph.error && <p className="message" style={{ padding: 16 }}>Non riesco a leggere il grafo: {graph.error}</p>}
          {graph.loading && !graph.data && (
            <div className="canvas-wait" role="status">
              <Icon name="loader" size={20} className="spin" />
              <span className="visually-hidden">Carico il grafo</span>
            </div>
          )}
          {graph.data && (
            <Graph3D
              handle={view}
              nodes={visible.nodes}
              links={visible.links}
              focus={focus}
              onNodeClick={(id) => setSelection({ kind: "node", id })}
              onLinkClick={(id) => setSelection({ kind: "edge", id })}
              onBackgroundClick={() => setSelection(null)}
            />
          )}
        </div>

        {(selectedEdge || selectedNode) && (
          <aside ref={evidencePanel} className="dock dock-right" aria-label="Prove">
            {selectedEdge && (
              <EdgeDetail
                edge={selectedEdge}
                nodes={nodes}
                onOpenPage={openPage}
                onSelectNode={(id) => setSelection({ kind: "node", id })}
                onClose={() => setSelection(null)}
              />
            )}
            {selectedNode && (
              <NodeDetail
                node={selectedNode}
                edges={edges}
                nodes={nodes}
                onOpenPage={openPage}
                onSelectEdge={(id) => setSelection({ kind: "edge", id })}
                onClose={() => setSelection(null)}
              />
            )}
          </aside>
        )}

        <footer className="statusbar">
          {graph.data && (
            <dl>
              <div>
                <dt>Nodi</dt>
                <dd>{formatNumber(graph.data.nodes.length)}</dd>
              </div>
              <div>
                <dt>Relazioni</dt>
                <dd>{formatNumber(knowledge.length)}</dd>
              </div>
              <div>
                <dt>Verificate</dt>
                <dd>{formatNumber(knowledge.filter((edge) => edge.tier === "green").length)}</dd>
              </div>
            </dl>
          )}
          <p className="statusbar-log">
            {!selection && graph.data && "Scegli un nodo o una relazione per vedere le prove."}
          </p>
        </footer>
      </div>

      {page && (
        <PageDialog
          manualId={manualId}
          page={page.page}
          marks={page.evidence.filter((item) => item.bbox).map((item) => ({ bbox: item.bbox! }))}
          onClose={() => setPage(null)}
        />
      )}
    </Shell>
  );
}
