// After an answer is applied or the graph approved, the run resumes for a few seconds to record it.
// The screens wait for that here, and then show the graph, instead of the run screen.
import { getJson } from "../api/client";
import type { Manual, Version } from "../api/types";

export async function settled(manualId: string, versionId: string, timeoutMs = 180_000, everyMs = 1_500): Promise<Version | null> {
  const until = Date.now() + timeoutMs;
  // The resume starts a moment after the request returns: give it the time to show as running.
  await new Promise((resolve) => setTimeout(resolve, everyMs));
  while (Date.now() < until) {
    const manual = await getJson<Manual>(`/api/manuals/${encodeURIComponent(manualId)}`).catch(() => null);
    const version = manual?.versions.find((item) => item.version_id === versionId);
    if (version && version.status !== "running") return version;
    await new Promise((resolve) => setTimeout(resolve, everyMs));
  }
  return null;
}
