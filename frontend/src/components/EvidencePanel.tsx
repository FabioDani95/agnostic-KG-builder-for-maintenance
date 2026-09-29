import type { Evidence, GraphEdge, GraphNode, Occurrence } from "../api/types";
import {
  CONDITION_PREFIX,
  formatNumber,
  RELATION_LABEL,
  REVIEWER_LABEL,
  TIER_LABEL,
  TYPE_LABEL,
  WITNESS_LABEL,
} from "../text/it";

export type OpenPage = (page: number, evidence: Evidence[]) => void;

function Quotes({ items, onOpenPage }: { items: Evidence[]; onOpenPage: OpenPage }) {
  const pages = [...new Set(items.map((item) => item.page))];
  return (
    <>
      <ul>
        {items.map((item) => (
          <li key={item.segment_id} className="quote-row">
            <span className="quote-page t-small num" style={{ textAlign: "left" }}>
              p. {item.page}
            </span>
            <span>{item.text}</span>
          </li>
        ))}
      </ul>
      {pages.map((page) => (
        <button
          key={page}
          type="button"
          className="button button-plain"
          style={{ paddingLeft: 0 }}
          onClick={() => onOpenPage(page, items.filter((item) => item.page === page))}
        >
          Apri la pagina {page}
        </button>
      ))}
    </>
  );
}

function decision(occurrence: Occurrence): string | null {
  const certificate = occurrence.certificate;
  const reviewer = certificate?.confirmed_by ?? certificate?.rejected_by;
  if (!certificate || !reviewer) return null;
  const who = reviewer.kind === "human" ? `una persona (${reviewer.name})` : REVIEWER_LABEL[reviewer.kind] ?? reviewer.kind;
  return `${certificate.confirmed_by ? "Confermata" : "Respinta"} da ${who}`;
}

export function EdgeDetail({
  edge,
  nodes,
  onOpenPage,
  onSelectNode,
}: {
  edge: GraphEdge;
  nodes: Map<string, GraphNode>;
  onOpenPage: OpenPage;
  onSelectNode: (id: string) => void;
}) {
  const from = nodes.get(edge.from);
  const to = nodes.get(edge.to);
  return (
    <div>
      <section className="panel-section">
        <h2 className="panel-title">Relazione</h2>
        <p className="t-large">
          <button type="button" className="button-plain list-button" style={{ display: "inline", minHeight: 0 }} onClick={() => onSelectNode(edge.from)}>
            «{from?.name}»
          </button>{" "}
          {RELATION_LABEL[edge.type] ?? edge.type}{" "}
          <button type="button" className="button-plain list-button" style={{ display: "inline", minHeight: 0 }} onClick={() => onSelectNode(edge.to)}>
            «{to?.name}»
          </button>
        </p>
        <dl className="data-list" style={{ gridTemplateColumns: "96px 1fr", marginTop: 16 }}>
          <dt>Stato</dt>
          <dd>{edge.derived ? "Aggiunta dal sistema" : TIER_LABEL[edge.tier]}</dd>
          <dt>Tipi</dt>
          <dd>
            {TYPE_LABEL[from?.type ?? ""]} e {TYPE_LABEL[to?.type ?? ""]?.toLowerCase()}
          </dd>
          <dt>Occorrenze</dt>
          <dd>{formatNumber(edge.occurrences.length)}</dd>
        </dl>
        {edge.derived && (
          <p className="message" style={{ marginTop: 16 }}>
            Collega la macchina ai suoi componenti e codici: la aggiunge il sistema, non viene dal testo.
          </p>
        )}
      </section>
      {edge.occurrences.map((occurrence, index) => (
        <section key={`${occurrence.record}-${index}`} className="panel-section">
          <h3 className="panel-title">
            Occorrenza {index + 1} di {edge.occurrences.length}
          </h3>
          {occurrence.certificate && (
            <dl className="data-list" style={{ gridTemplateColumns: "96px 1fr", marginBottom: 16 }}>
              <dt>Stato</dt>
              <dd>{occurrence.tier ? TIER_LABEL[occurrence.tier] : ""}</dd>
              <dt>Testimoni</dt>
              <dd>
                {occurrence.certificate.witnesses.map((witness) => WITNESS_LABEL[witness] ?? witness).join(", ") ||
                  "nessuno"}
              </dd>
              {decision(occurrence) && (
                <>
                  <dt>Decisione</dt>
                  <dd>{decision(occurrence)}</dd>
                </>
              )}
            </dl>
          )}
          {(occurrence.conditions ?? []).map((condition, conditionIndex) => (
            <p key={conditionIndex} className="t-body" style={{ marginBottom: 8 }}>
              {CONDITION_PREFIX[condition.kind] ?? "Vale se"}: {condition.text}
            </p>
          ))}
          <Quotes items={occurrence.evidence} onOpenPage={onOpenPage} />
        </section>
      ))}
    </div>
  );
}

export function NodeDetail({
  node,
  edges,
  nodes,
  onOpenPage,
  onSelectEdge,
}: {
  node: GraphNode;
  edges: GraphEdge[];
  nodes: Map<string, GraphNode>;
  onOpenPage: OpenPage;
  onSelectEdge: (id: string) => void;
}) {
  const touching = edges.filter((edge) => edge.from === node.id || edge.to === node.id);
  const pages = [...new Set(node.evidence.map((item) => item.page))].sort((a, b) => a - b);
  return (
    <div>
      <section className="panel-section">
        <h2 className="panel-title">{node.name}</h2>
        <dl className="data-list" style={{ gridTemplateColumns: "96px 1fr" }}>
          <dt>Tipo</dt>
          <dd>{TYPE_LABEL[node.type] ?? node.type}</dd>
          {pages.length > 0 && (
            <>
              <dt>Pagine</dt>
              <dd>{pages.join(", ")}</dd>
            </>
          )}
          {node.type === "FailureMode" && node.stated_in_source === false && (
            <>
              <dt>Nome</dt>
              <dd>Causa non scritta nel manuale: il nome lo ha dato il sistema</dd>
            </>
          )}
          {(node.aliases ?? []).length > 0 && (
            <>
              <dt>Altri nomi</dt>
              <dd>{node.aliases!.join("; ")}</dd>
            </>
          )}
        </dl>
      </section>
      {node.evidence.length > 0 && (
        <section className="panel-section">
          <h3 className="panel-title">Nel manuale</h3>
          <Quotes items={node.evidence} onOpenPage={onOpenPage} />
        </section>
      )}
      {touching.length > 0 && (
        <section className="panel-section">
          <h3 className="panel-title">Relazioni</h3>
          <ul className="stage-list">
            {touching.map((edge) => {
              const other = nodes.get(edge.from === node.id ? edge.to : edge.from);
              const text =
                edge.from === node.id
                  ? `${RELATION_LABEL[edge.type] ?? edge.type} «${other?.name}»`
                  : `«${other?.name}» ${RELATION_LABEL[edge.type] ?? edge.type}`;
              return (
                <li key={edge.id}>
                  <button type="button" className="list-button" onClick={() => onSelectEdge(edge.id)}>
                    <span className="t-body" style={{ display: "block" }}>
                      {text}
                    </span>
                    <span className="t-small secondary">
                      {edge.derived ? "Aggiunta dal sistema" : TIER_LABEL[edge.tier]}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </section>
      )}
    </div>
  );
}
