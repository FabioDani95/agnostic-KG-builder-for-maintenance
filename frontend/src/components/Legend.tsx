import { NODE_STYLE, NODE_TYPES } from "../graph/style";
import { formatNumber, TYPE_LABEL } from "../text/it";

/** Key of the graph colors: the one place outside the graph where colored circles appear. */
export function Legend({ counts }: { counts?: Record<string, number> }) {
  return (
    <ul className="legend t-small" aria-label="Legenda dei tipi di nodo">
      {NODE_TYPES.map((type) => (
        <li key={type}>
          <span className="legend-mark" style={{ background: NODE_STYLE[type].color }} aria-hidden="true" />
          <span style={{ flex: 1 }}>{TYPE_LABEL[type]}</span>
          {counts && <span className="num secondary">{formatNumber(counts[type] ?? 0)}</span>}
        </li>
      ))}
    </ul>
  );
}
