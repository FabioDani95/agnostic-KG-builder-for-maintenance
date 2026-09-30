import { useCallback, useEffect, useState } from "react";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function detail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return typeof body.detail === "string" ? body.detail : response.statusText;
  } catch {
    return response.statusText;
  }
}

export const OFFLINE = "Il server non risponde: controlla che scripts/ui.py sia avviato.";

/** fetch, with a sentence a person can act on when the server is not there at all. */
async function request(url: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(url, init);
  } catch {
    throw new ApiError(0, OFFLINE);
  }
}

export async function getJson<T>(url: string): Promise<T> {
  const response = await request(url);
  if (!response.ok) throw new ApiError(response.status, await detail(response));
  return response.json() as Promise<T>;
}

export async function postJson<T>(url: string, body?: unknown): Promise<T> {
  const response = await request(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) throw new ApiError(response.status, await detail(response));
  return response.json() as Promise<T>;
}

export const versionPath = (manualId: string, versionId: string) =>
  `/api/manuals/${encodeURIComponent(manualId)}/versions/${encodeURIComponent(versionId)}`;

// Screens of the interface, in one place.
export const manualRoute = (manualId: string) => `/manuali/${encodeURIComponent(manualId)}`;
export const graphRoute = (manualId: string, versionId: string) =>
  `${manualRoute(manualId)}/versioni/${encodeURIComponent(versionId)}`;
export const liveRoute = (manualId: string, versionId: string) => `${graphRoute(manualId, versionId)}/esecuzione`;
export const questionsRoute = (manualId: string, versionId: string) => `${graphRoute(manualId, versionId)}/domande`;

export interface Loaded<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  reload: () => void;
}

/** Fetch JSON when the URL changes; `null` skips the request. */
export function useApi<T>(url: string | null): Loaded<T> {
  const [state, setState] = useState<{ data: T | null; error: string | null; loading: boolean }>({
    data: null,
    error: null,
    loading: url !== null,
  });
  const [round, setRound] = useState(0);
  useEffect(() => {
    if (url === null) return;
    let current = true;
    setState((previous) => ({ ...previous, loading: true, error: null }));
    getJson<T>(url)
      .then((data) => current && setState({ data, error: null, loading: false }))
      .catch((error: Error) => current && setState({ data: null, error: error.message, loading: false }));
    return () => {
      current = false;
    };
  }, [url, round]);
  const reload = useCallback(() => setRound((value) => value + 1), []);
  return { ...state, reload };
}
