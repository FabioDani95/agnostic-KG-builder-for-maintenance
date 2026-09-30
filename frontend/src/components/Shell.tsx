import { Fragment, type ReactNode, useEffect } from "react";
import { Link, NavLink } from "react-router-dom";
import { liveRoute } from "../api/client";
import { useStatus } from "../status/StatusProvider";
import { APP_NAME } from "../text/it";
import { Icon, type IconName, Logo } from "./Icon";

export interface Crumb {
  to: string;
  label: string;
}

const NAV: { to: string; label: string; icon: IconName }[] = [
  { to: "/tocca-a-te", label: "Tocca a te", icon: "inbox" },
  { to: "/esecuzioni", label: "Esecuzioni", icon: "activity" },
  { to: "/ontologia", label: "Ontologia", icon: "schema" },
];

/**
 * The rail leads to places; the path bar holds what can be done on the page. The logo is the
 * way home (all the graphs). Below the places: the run in progress, always in sight.
 */
function Rail() {
  const status = useStatus();
  const waiting = status.inbox?.waiting.length ?? 0;
  const active = status.active;

  return (
    <nav className="rail" aria-label="Sezioni">
      <Link to="/" className="rail-brand" aria-label={`${APP_NAME}: tutti i grafi`} data-tip="Tutti i grafi">
        <Logo />
      </Link>
      {NAV.map((item) => {
        const count = item.to === "/tocca-a-te" ? waiting : 0;
        return (
          <NavLink
            key={item.to}
            to={item.to}
            className="rail-item"
            data-tip={count ? `${item.label}: ${count}` : item.label}
            aria-label={count ? `${item.label}, ${count} in attesa` : item.label}
          >
            <Icon name={item.icon} size={20} />
            {count > 0 && <span className="rail-badge">{count}</span>}
          </NavLink>
        );
      })}
      <span className="rail-fill" />
      {active && (
        <Link
          to={liveRoute(active.manualId, active.versionId)}
          className="rail-item rail-live"
          data-tip={`In corso: ${active.name}`}
          aria-label={`Esecuzione in corso: ${active.name}`}
        >
          <span className="live-lamp" aria-hidden="true" />
        </Link>
      )}
    </nav>
  );
}

/**
 * The frame of every screen: the rail, then a path bar that names the page and holds its actions
 * on the right (add, approve, replay). Graph screens pass `workspace` and fill the rest themselves;
 * the others get a scrolling content area.
 */
export function Shell({
  trail = [],
  title,
  actions,
  workspace = false,
  children,
}: {
  trail?: Crumb[];
  title: string;
  actions?: ReactNode;
  workspace?: boolean;
  children?: ReactNode;
}) {
  useEffect(() => {
    document.title = title ? `${title} · ${APP_NAME}` : APP_NAME;
  }, [title]);

  return (
    <div className="shell">
      <Rail />
      <div className="shell-main">
        <header className="crumbs">
          <nav className="crumbs-path" aria-label="Percorso">
            {trail.map((crumb) => (
              <Fragment key={crumb.to}>
                <Link to={crumb.to} className="crumb">
                  {crumb.label}
                </Link>
                <span className="crumb-sep" aria-hidden="true">
                  <Icon name="chevron-right" size={14} />
                </span>
              </Fragment>
            ))}
            <h1 className="crumb-title" title={title}>
              {title}
            </h1>
          </nav>
          {actions && <div className="crumbs-actions">{actions}</div>}
        </header>
        {workspace ? children : <main className="content">{children}</main>}
      </div>
    </div>
  );
}
