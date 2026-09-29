import { useEffect, useReducer, useRef, useState } from "react";
import type { UiEvent } from "./events";
import { initialRun, runReducer } from "./reducer";

const FINAL = new Set(["run_finished", "run_failed"]);

/**
 * Follow the events of a run over SSE. Pausing closes the stream; resuming opens it again
 * after the last event seen, so nothing is lost or repeated.
 */
export function useRunStream(url: string | null, speed: number, paused: boolean) {
  const [state, dispatch] = useReducer(runReducer, undefined, initialRun);
  const lastSeq = useRef(0);
  const ended = useRef(false);
  const [arrivedAt, setArrivedAt] = useState(() => performance.now());
  const [unavailable, setUnavailable] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!url || paused || ended.current) return;
    const source = new EventSource(`${url}?speed=${speed}&from=${lastSeq.current}`);
    let received = false;
    source.onmessage = (message) => {
      received = true;
      const event = JSON.parse(message.data) as UiEvent;
      lastSeq.current = Math.max(lastSeq.current, event.seq);
      setArrivedAt(performance.now());
      dispatch(event);
      if (FINAL.has(event.kind)) {
        ended.current = true;
        source.close();
      }
    };
    let retry = 0;
    source.onerror = () => {
      source.close();
      // Never started: nothing to replay here. Cut in the middle: try again after the last event.
      if (!received && lastSeq.current === 0) setUnavailable(true);
      else if (!ended.current) retry = window.setTimeout(() => setAttempt((value) => value + 1), 2000);
    };
    return () => {
      window.clearTimeout(retry);
      source.close();
    };
  }, [url, speed, paused, attempt]);

  return { state, arrivedAt, unavailable };
}
