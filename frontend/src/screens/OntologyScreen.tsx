import { useApi } from "../api/client";
import type { Ontology, OntologyRelation } from "../api/types";
import { Loading, Problem } from "../components/Feedback";
import { Shell } from "../components/Shell";
import { EDGE_STYLE, NODE_STYLE } from "../graph/style";
import { formatNumber, RELATION_LABEL, TYPE_LABEL } from "../text/it";
import { tr } from "../i18n/i18n";

const BOX = { width: 150, height: 40 };
const WIDTH = 900;
const ROW = 160; // vertical room of one column
const TOP = 60;

/** Columns by longest path from the types nothing points to; order inside a column by the rows it comes from. */
export function schemaLayout(names: string[], relations: Pick<OntologyRelation, "domain" | "range">[]) {
  const layer = new Map(names.map((name) => [name, 0]));
  for (let round = 0; round < names.length; round += 1) {
    for (const relation of relations) {
      const next = (layer.get(relation.domain) ?? 0) + 1;
      if (next > (layer.get(relation.range) ?? 0)) layer.set(relation.range, next);
    }
  }
  const columns = Math.max(...layer.values()) + 1;
  const position = new Map<string, { x: number; y: number }>();
  const step = columns > 1 ? (WIDTH - BOX.width - 40) / (columns - 1) : 0;
  for (let column = 0; column < columns; column += 1) {
    const members = names.filter((name) => layer.get(name) === column);
    const weight = (name: string) => {
      const from = relations.filter((relation) => relation.range === name).map((relation) => position.get(relation.domain)?.y);
      const known = from.filter((value): value is number => value !== undefined);
      return known.length ? known.reduce((sum, value) => sum + value, 0) / known.length : names.indexOf(name);
    };
    if (column > 0) members.sort((a, b) => weight(a) - weight(b));
    members.forEach((name, index) => {
      const y = members.length === 1 ? TOP + ROW / 2 : TOP + (ROW * index) / (members.length - 1);
      position.set(name, { x: 20 + BOX.width / 2 + column * step, y });
    });
  }
  return { position, height: TOP * 2 + ROW };
}

function SchemaDiagram({ schema }: { schema: Ontology }) {
  const names = schema.nodes.map((node) => node.name);
  const { position, height } = schemaLayout(names, schema.relations);
  return (
    <svg
      className="schema"
      viewBox={`0 0 ${WIDTH} ${height}`}
      role="img"
      aria-label={tr("Schema del grafo: i tipi di nodo e le relazioni tra loro")}
    >
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0 0 10 5 0 10z" fill="#a8a29e" />
        </marker>
      </defs>
      {schema.relations.map((relation) => {
        const from = position.get(relation.domain)!;
        const to = position.get(relation.range)!;
        const x1 = from.x + BOX.width / 2;
        const x2 = to.x - BOX.width / 2;
        const bend = Math.max(40, (x2 - x1) / 2);
        const path = `M${x1} ${from.y} C${x1 + bend} ${from.y} ${x2 - bend} ${to.y} ${x2} ${to.y}`;
        const label = RELATION_LABEL[relation.name] ?? relation.name;
        const mx = (x1 + x2) / 2;
        const my = (from.y + to.y) / 2;
        return (
          <g key={relation.name}>
            <path
              d={path}
              fill="none"
              stroke={relation.added_by_code ? EDGE_STYLE.derived.color : "#a8a29e"}
              strokeWidth={1.5}
              strokeDasharray={relation.added_by_code ? "5 4" : undefined}
              markerEnd="url(#arrow)"
            />
            <rect x={mx - label.length * 3.4 - 6} y={my - 9} width={label.length * 6.8 + 12} height={18} rx={3} className="schema-tag" />
            <text x={mx} y={my + 4} textAnchor="middle" className="schema-edge-label">
              {label}
            </text>
          </g>
        );
      })}
      {schema.nodes.map((node) => {
        const at = position.get(node.name)!;
        const color = NODE_STYLE[node.name]?.color ?? "#8e8e93";
        return (
          <g key={node.name} transform={`translate(${at.x - BOX.width / 2} ${at.y - BOX.height / 2})`}>
            <rect width={BOX.width} height={BOX.height} rx={4} className="schema-node" style={{ stroke: color }} />
            <circle cx={16} cy={BOX.height / 2} r={5} fill={color} />
            <text x={30} y={17} className="schema-node-label">
              {TYPE_LABEL[node.name] ?? node.name}
            </text>
            <text x={30} y={31} className="schema-node-code">
              {node.name}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

/**
 * The fixed schema every graph follows, read from the same file the runs read. The diagram uses
 * the colors of the 3D graph, so it doubles as the key to read it.
 */
export function OntologyScreen() {
  const { data: schema, error, loading, reload } = useApi<Ontology>("/api/ontology");
  const label = (name: string) => TYPE_LABEL[name] ?? name;

  return (
    <Shell title={tr("Ontologia")}>
      {error && <Problem message={`${tr("Non riesco a leggere lo schema.")} ${error}`} onRetry={reload} />}
      {loading && !schema && <Loading label={tr("Carico lo schema")} />}
      {schema && (
        <div className="stack">
          <section className="card">
            <header className="card-head">
              <h2 className="card-title">{tr("Schema del grafo")}</h2>
              <span className="t-small secondary">
                {tr("Ogni esecuzione legge")} <span className="mono">ontology_schema.JSON</span>
                {tr(": il grafo contiene solo questi tipi e queste relazioni.")}
              </span>
            </header>
            <div className="schema-frame">
              <SchemaDiagram schema={schema} />
            </div>
            <div className="card-actions t-small secondary">
              <span className="schema-key" data-kind="extracted" /> {tr("Estratta dal modello, con le sue prove nel manuale")}
              <span className="schema-key" data-kind="code" style={{ marginLeft: 16 }} />{" "}
              {tr("Aggiunta dal codice: lega la macchina ai suoi componenti e codici")}
            </div>
          </section>

          <section className="card">
            <header className="card-head">
              <h2 className="card-title">
                {tr("Tipi di nodo")} <span className="card-count">{formatNumber(schema.nodes.length)}</span>
              </h2>
            </header>
            <ul className="schema-list">
              {schema.nodes.map((node) => (
                <li key={node.name}>
                  <span className="with-mark">
                    <span className="legend-mark" style={{ background: NODE_STYLE[node.name]?.color }} aria-hidden="true" />
                    <span className="strong">{label(node.name)}</span>
                  </span>
                  <span className="mono secondary">{node.name}</span>
                  <span>
                    {node.description}
                    {node.name === schema.root && <span className="secondary"> {tr("È la radice: una per grafo.")}</span>}
                  </span>
                  <span className="mono t-small secondary">
                    {node.properties.map((prop) => `${prop.name}${prop.required ? "*" : ""}`).join(" · ")}
                  </span>
                </li>
              ))}
            </ul>
            <p className="card-actions t-small secondary">{tr("Le proprietà con * sono obbligatorie. Le descrizioni sono quelle dello schema.")}</p>
          </section>

          <section className="card">
            <header className="card-head">
              <h2 className="card-title">
                {tr("Relazioni")} <span className="card-count">{formatNumber(schema.relations.length)}</span>
              </h2>
            </header>
            <ul className="schema-list">
              {schema.relations.map((relation) => (
                <li key={relation.name}>
                  <span>
                    <span className="strong">{label(relation.domain)}</span> {RELATION_LABEL[relation.name] ?? relation.name}{" "}
                    <span className="strong">{label(relation.range)}</span>
                  </span>
                  <span className="mono secondary">{relation.name}</span>
                  <span>{relation.description}</span>
                  <span className="t-small secondary">
                    {tr(relation.added_by_code ? "Aggiunta dal codice" : "Estratta dal modello")}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </Shell>
  );
}
