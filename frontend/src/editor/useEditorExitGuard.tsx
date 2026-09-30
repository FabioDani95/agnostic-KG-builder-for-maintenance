import { useEffect, type RefObject } from "react";
import { useBlocker } from "react-router-dom";
import { tr, useLang } from "../i18n/i18n";
import { useEditor } from "./EditorSessionProvider";
import { dirty } from "./reducer";
export function useEditorExitGuard(
  pathname: string,
  bypass: RefObject<boolean>,
) {
  useLang();
  const { state, dispatch } = useEditor();
  const protectedDraft = dirty(state) || state.pending;
  const blocker = useBlocker(
    ({ nextLocation }) =>
      !bypass.current &&
      nextLocation.pathname !== pathname &&
      (protectedDraft || state.saving),
  );
  useEffect(() => {
    const unload = (event: BeforeUnloadEvent) => {
      if (protectedDraft || state.saving) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    const hide = () => dispatch({ type: "reset" });
    const show = (event: PageTransitionEvent) => {
      if (event.persisted) dispatch({ type: "reset" });
    };
    window.addEventListener("beforeunload", unload);
    window.addEventListener("pagehide", hide);
    window.addEventListener("pageshow", show);
    return () => {
      window.removeEventListener("beforeunload", unload);
      window.removeEventListener("pagehide", hide);
      window.removeEventListener("pageshow", show);
    };
  }, [protectedDraft, state.saving, dispatch]);
  useEffect(() => {
    if (blocker.state === "blocked" && state.saving) blocker.reset();
  }, [blocker, state.saving]);
  return blocker.state === "blocked" && !state.saving ? (
    <div className="editor-exit-overlay">
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="exit-title"
        className="card editor-exit"
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            event.preventDefault();
            blocker.reset();
          }
          if (event.key === "Tab") {
            const buttons = event.currentTarget.querySelectorAll("button");
            if (event.shiftKey && document.activeElement === buttons[0]) {
              event.preventDefault();
              buttons[buttons.length - 1].focus();
            } else if (
              !event.shiftKey &&
              document.activeElement === buttons[buttons.length - 1]
            ) {
              event.preventDefault();
              buttons[0].focus();
            }
          }
        }}
      >
        <h2 id="exit-title">
          {tr("Uscire senza salvare? Le modifiche saranno perse.")}
        </h2>
        <button
          autoFocus
          className="button button-secondary"
          onClick={() => blocker.reset()}
        >
          {tr("Continua a modificare")}
        </button>
        <button
          className="button button-primary"
          onClick={() => {
            dispatch({ type: "reset" });
            blocker.proceed();
          }}
        >
          {tr("Esci e scarta")}
        </button>
      </div>
    </div>
  ) : null;
}
