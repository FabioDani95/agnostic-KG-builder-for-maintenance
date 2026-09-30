import { Fragment, type ReactNode, useEffect, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { liveRoute } from "../api/client";
import { useStatus } from "../status/StatusProvider";
import { appName } from "../text/it";
import { Icon, type IconName, Logo } from "./Icon";
import { SettingsDialog } from "./SettingsDialog";
import { tr, useLang } from "../i18n/i18n";

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
  const [settingsOpen, setSettingsOpen] = useState(false);
  const { lang, change } = useLang();
  const waiting = status.inbox?.waiting.length ?? 0;
  const active = status.active;

  return (
    <nav className="rail" aria-label={tr("Sezioni")}>
      <Link to="/" className="rail-brand" aria-label={tr("{app}: tutti i grafi", { app: appName() })} data-tip={tr("Tutti i grafi")}>
        <Logo />
      </Link>
      {NAV.map((item) => {
        const count = item.to === "/tocca-a-te" ? waiting : 0;
        return (
          <NavLink
            key={item.to}
            to={item.to}
            className="rail-item"
            data-tip={count ? `${tr(item.label)}: ${count}` : tr(item.label)}
            aria-label={count ? tr("{label}, {count} in attesa", { label: tr(item.label), count }) : tr(item.label)}
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
          data-tip={tr("In corso: {name}", { name: active.name })}
          aria-label={tr("Esecuzione in corso: {name}", { name: active.name })}
        >
          <span className="live-lamp" aria-hidden="true" />
        </Link>
      )}
      <button
        type="button"
        className="rail-item rail-lang"
        data-tip={lang === "it" ? "English" : "Italiano"}
        aria-label={lang === "it" ? "Switch to English" : "Passa all'italiano"}
        onClick={() => change(lang === "it" ? "en" : "it")}
      >
        {lang.toUpperCase()}
      </button>
      <NavLink to="/guida" className="rail-item" data-tip={tr("Guida")} aria-label={tr("Guida")}>
        <Icon name="question" size={20} />
      </NavLink>
      <button
        type="button"
        className="rail-item rail-settings"
        data-tip={tr("Impostazioni")}
        aria-label={tr("Impostazioni")}
        aria-haspopup="dialog"
        disabled={!status.settings}
        onClick={() => setSettingsOpen(true)}
      >
        <Icon name="settings" size={20} />
      </button>
      {settingsOpen && status.settings && (
        <SettingsDialog settings={status.settings} onClose={() => setSettingsOpen(false)} onSaved={status.refresh} />
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
    document.title = title ? `${tr(title)} · ${appName()}` : appName();
  }, [title]);

  return (
    <div className="shell">
      <Rail />
      <div className="shell-main">
        <header className="crumbs">
          <nav className="crumbs-path" aria-label={tr("Percorso")}>
            {trail.map((crumb) => (
              <Fragment key={crumb.to}>
                <Link to={crumb.to} className="crumb">
                  {tr(crumb.label)}
                </Link>
                <span className="crumb-sep" aria-hidden="true">
                  <Icon name="chevron-right" size={14} />
                </span>
              </Fragment>
            ))}
            <h1 className="crumb-title" title={tr(title)}>
              {tr(title)}
            </h1>
          </nav>
          {actions && <div className="crumbs-actions">{actions}</div>}
        </header>
        {workspace ? children : <main className="content">{children}</main>}
      </div>
    </div>
  );
}
