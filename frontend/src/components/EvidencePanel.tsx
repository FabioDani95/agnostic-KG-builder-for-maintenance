import type { Evidence, GraphEdge, GraphNode, Occurrence } from "../api/types";
import { Icon } from "./Icon";
import {
  CONDITION_PREFIX,
  formatNumber,
  RELATION_LABEL,
  REVIEWER_LABEL,
  TIER_LABEL,
  TYPE_LABEL,
  WITNESS_LABEL,
} from "../text/it";
import { tr } from "../i18n/i18n";

export type OpenPage = (page: number, evidence: Evidence[]) => void;

function PanelHead({ title, onClose }: { title: string; onClose: () => void }) {
  return (
    <div className="panel-head">
      <h2 className="panel-title">{title}</h2>
      <button type="button" className="button button-secondary button-icon" aria-label={tr("Chiudi")} onClick={onClose}>
        <Icon name="x" />
      </button>
    </div>
  );
}

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
          <Icon name="external-link" size={14} />
          {tr("Apri la pagina {page}", { page: page })}
        </button>
      ))}
    </>
  );
}

function decision(occurrence: Occurrence): string | null {
  const certificate = occurrence.certificate;
  const reviewer = certificate?.confirmed_by ?? certificate?.rejected_by;
  if (!certificate || !reviewer) return null;
  const who = reviewer.kind === "human" ? tr("una persona ({name})", { name: reviewer.name }) : REVIEWER_LABEL[reviewer.kind] ?? reviewer.kind;
  return tr(certificate.confirmed_by ? "Confermata da {who}" : "Respinta da {who}", { who });
}

export function EdgeDetail({
  edge,
  nodes,
  onOpenPage,
  onSelectNode,
  onClose,
}: {
  edge: GraphEdge;
  nodes: Map<string, GraphNode>;
  onOpenPage: OpenPage;
  onSelectNode: (id: string) => void;
  onClose: () => void;
}) {
  const from = nodes.get(edge.from);
  const to = nodes.get(edge.to);
  return (
    <div>
      <section className="panel-section">
        <PanelHead title={tr("Relazione")} onClose={onClose} />
        <p className="panel-name">
          <button type="button" className="button-plain list-button" style={{ display: "inline", minHeight: 0 }} onClick={() => onSelectNode(edge.from)}>
            «{from?.name}»
          </button>{" "}
          {RELATION_LABEL[edge.type] ?? edge.type}{" "}
          <button type="button" className="button-plain list-button" style={{ display: "inline", minHeight: 0 }} onClick={() => onSelectNode(edge.to)}>
            «{to?.name}»
          </button>
        </p>
        <dl className="data-list" style={{ gridTemplateColumns: "96px 1fr", marginTop: 8 }}>
          <dt>{tr("Stato")}</dt>
          <dd>{edge.derived ? tr("Aggiunta dal sistema") : TIER_LABEL[edge.tier]}</dd>
          <dt>{tr("Tipi")}</dt>
          <dd>
            {tr("{a} e {b}", { a: TYPE_LABEL[from?.type ?? ""] ?? "", b: TYPE_LABEL[to?.type ?? ""]?.toLowerCase() ?? "" })}
          </dd>
          <dt>{tr("Occorrenze")}</dt>
          <dd>{formatNumber(edge.occurrences.length)}</dd>
        </dl>
        {edge.derived && (
          <p className="message" style={{ marginTop: 16 }}>
            {tr("Collega la macchina ai suoi componenti e codici: la aggiunge il sistema, non viene dal testo.")}
          </p>
        )}
      </section>
      {edge.occurrences.map((occurrence, index) => (
        <section key={`${occurrence.record}-${index}`} className="panel-section">
          <h3 className="panel-title">
            {tr("Occorrenza {n} di {total}", { n: index + 1, total: edge.occurrences.length })}
          </h3>
          {occurrence.certificate && (
            <dl className="data-list" style={{ gridTemplateColumns: "96px 1fr", marginBottom: 8 }}>
              <dt>{tr("Stato")}</dt>
              <dd>{occurrence.tier ? TIER_LABEL[occurrence.tier] : ""}</dd>
              <dt>{tr("Testimoni")}</dt>
              <dd>
                {occurrence.certificate.witnesses.map((witness) => WITNESS_LABEL[witness] ?? witness).join(", ") ||
                  tr("nessuno")}
              </dd>
              {decision(occurrence) && (
                <>
                  <dt>{tr("Decisione")}</dt>
                  <dd>{decision(occurrence)}</dd>
                </>
              )}
            </dl>
          )}
          {(occurrence.conditions ?? []).map((condition, conditionIndex) => (
            <p key={conditionIndex} className="t-body" style={{ marginBottom: 8 }}>
              {CONDITION_PREFIX[condition.kind] ?? tr("Vale se")}: {condition.text}
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
  onClose,
}: {
  node: GraphNode;
  edges: GraphEdge[];
  nodes: Map<string, GraphNode>;
  onOpenPage: OpenPage;
  onSelectEdge: (id: string) => void;
  onClose: () => void;
}) {
  const touching = edges.filter((edge) => edge.from === node.id || edge.to === node.id);
  const pages = [...new Set(node.evidence.map((item) => item.page))].sort((a, b) => a - b);
  return (
    <div>
      <section className="panel-section">
        <PanelHead title={TYPE_LABEL[node.type] ?? node.type} onClose={onClose} />
        <p className="panel-name">{node.name}</p>
        <dl className="data-list" style={{ gridTemplateColumns: "96px 1fr" }}>
          {pages.length > 0 && (
            <>
              <dt>{tr("Pagine")}</dt>
              <dd className="mono">{pages.join(", ")}</dd>
            </>
          )}
          {node.type === "FailureMode" && node.stated_in_source === false && (
            <>
              <dt>{tr("Nome")}</dt>
              <dd>{tr("Causa non scritta nel manuale: il nome lo ha dato il sistema")}</dd>
            </>
          )}
          {(node.aliases ?? []).length > 0 && (
            <>
              <dt>{tr("Altri nomi")}</dt>
              <dd>{node.aliases!.join("; ")}</dd>
            </>
          )}
        </dl>
      </section>
      {node.evidence.length > 0 && (
        <section className="panel-section">
          <h3 className="panel-title">{tr("Nel manuale")}</h3>
          <Quotes items={node.evidence} onOpenPage={onOpenPage} />
        </section>
      )}
      {touching.length > 0 && (
        <section className="panel-section">
          <h3 className="panel-title">{tr("Relazioni")}</h3>
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
                      {edge.derived ? tr("Aggiunta dal sistema") : TIER_LABEL[edge.tier]}
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
