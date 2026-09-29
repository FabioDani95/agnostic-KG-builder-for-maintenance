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

export async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new ApiError(response.status, await detail(response));
  return response.json() as Promise<T>;
}

export async function postJson<T>(url: string, body?: unknown): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) throw new ApiError(response.status, await detail(response));
  return response.json() as Promise<T>;
}

export const versionPath = (manualId: string, versionId: string) =>
  `/api/manuals/${encodeURIComponent(manualId)}/versions/${encodeURIComponent(versionId)}`;

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
