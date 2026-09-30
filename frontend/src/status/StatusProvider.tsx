import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import { getJson } from "../api/client";
import type { ActiveJob, ManualRow, Preferences } from "../api/types";
import { activeVersion, inbox, type Inbox } from "../flow/steps";
import { manualName } from "../text/it";

export interface Status {
  manuals: ManualRow[] | null;
  /** Why the manuals could not be read, while there is nothing older to show. */
  error: string | null;
  inbox: Inbox | null;
  active: { manualId: string; versionId: string; name: string } | null;
  settings: Preferences | null;
  refresh: () => void;
}

const EMPTY: Status = { manuals: null, error: null, inbox: null, active: null, settings: null, refresh: () => undefined };
const StatusContext = createContext<Status>(EMPTY);
const EVERY_MS = 10_000;

/**
 * What the frame shows on every screen: the run in progress and the graphs that
 * wait for a person. Read again on each change of screen and every 10 s while the tab is visible.
 */
export function StatusProvider({ children }: { children: ReactNode }) {
  const location = useLocation();
  const [round, setRound] = useState(0);
  const [data, setData] = useState<Omit<Status, "refresh" | "inbox">>({ manuals: null, error: null, active: null, settings: null });

  useEffect(() => {
    let current = true;
    Promise.allSettled([
      getJson<ManualRow[]>("/api/manuals"),
      getJson<ActiveJob>("/api/jobs/active"),
      getJson<Preferences>("/api/settings"),
    ]).then(([manuals, job, preferences]) => {
      if (!current) return;
      setData((previous) => {
        const rows = manuals.status === "fulfilled" ? manuals.value : previous.manuals;
        const running = job.status === "fulfilled" ? activeVersion(job.value.run) : previous.active;
        const found = running ? rows?.find((row) => row.id === running.manualId) : undefined;
        const name = found ? manualName(found.machine) : running?.manualId ?? "";
        return {
          manuals: rows,
          error: manuals.status === "rejected" && !rows ? (manuals.reason as Error).message : null,
          active: running ? { ...running, name } : null,
          settings: preferences.status === "fulfilled" ? preferences.value : previous.settings,
        };
      });
    });
    return () => {
      current = false;
    };
  }, [round, location.pathname]);

  useEffect(() => {
    const tick = () => document.visibilityState === "visible" && setRound((value) => value + 1);
    const timer = window.setInterval(tick, EVERY_MS);
    document.addEventListener("visibilitychange", tick);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", tick);
    };
  }, []);

  const refresh = useCallback(() => setRound((value) => value + 1), []);
  const value = useMemo<Status>(
    () => ({ ...data, inbox: data.manuals ? inbox(data.manuals) : null, refresh }),
    [data, refresh],
  );
  return <StatusContext.Provider value={value}>{children}</StatusContext.Provider>;
}

export const useStatus = () => useContext(StatusContext);
