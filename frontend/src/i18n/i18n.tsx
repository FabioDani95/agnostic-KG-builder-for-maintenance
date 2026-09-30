// The language of the interface. The Italian text is the key; the English dictionary gives its
// translation. Context refreshes text without remounting a graph editing session.
import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { EN } from "./en";

export type Lang = "it" | "en";
const KEY = "lang";

function saved(): Lang {
  try {
    return window.localStorage.getItem(KEY) === "en" ? "en" : "it";
  } catch {
    return "it";
  }
}

let current: Lang = typeof window === "undefined" ? "it" : saved();

export const getLang = () => current;
export const locale = () => (current === "en" ? "en-GB" : "it-IT");

/** The text in the language of the interface; {name} marks are filled from `values`. */
const CODE_TEXT: Record<string,string> = {
  "INVALID_OPERATION": "La modifica contiene dati non validi. Controlla i campi indicati.",
  "BASE_CHANGED": "La base, lo schema o la fonte sono cambiati. Riapri l’editor sulla base attuale.",
  "STALE_PREVIEW": "Il riepilogo è obsoleto. Ripeti i controlli.",
  "ACKNOWLEDGEMENT_REQUIRED": "Riconosci i dubbi residui prima di accettare.",
  "NO_CHANGES": "Nessuna modifica da salvare",
  "REQUEST_ID_CONFLICT": "Questa richiesta è già stata usata con un contenuto diverso.",
  "VALIDATION_FAILED": "Risolvi gli errori bloccanti prima dell’accettazione.",
  "PROCESS_RUNNING": "Disponibile al termine dell’estrazione",
  "UNAPPLIED_ANSWERS": "Applica prima le risposte",
  "GRAPH_UNAVAILABLE": "Grafo assente o formato non supportato",
  "SOURCE_SEGMENT_UNAVAILABLE": "Segmento della fonte non disponibile",
  "RESERVED_FIELD": "Il campo è in sola lettura o fuori schema.",
  "ROOT_PROTECTED": "La macchina radice non può essere eliminata.",
  "STALE_OCCURRENCE": "L’occorrenza è cambiata dopo la conferma.",
  "NODE_NOT_FOUND": "Nodo non trovato",
  "EDGE_NOT_FOUND": "Relazione non trovata",
  "OCCURRENCE_NOT_FOUND": "Occorrenza non trovata",
  "UNSUPPORTED_GRAPH": "Formato del grafo non supportato",
  "DUPLICATE_ID": "ID duplicato",
  "NODE_TYPE": "Tipo di nodo non ammesso",
  "REQUIRED_FIELD": "Campo obbligatorio assente o vuoto",
  "DERIVED_READ_ONLY": "Relazione aggiunta dal sistema: sola lettura"
};

export function tr(text: string, values?: Record<string, string | number>): string {
  const translated = current === "en" ? (EN[text] ?? EN[CODE_TEXT[text]] ?? CODE_TEXT[text] ?? text) : (CODE_TEXT[text] ?? text);
  return values ? translated.replace(/\{(\w+)\}/g, (mark, name) => (name in values ? String(values[name]) : mark)) : translated;
}

/** For tests and the switch itself. */
export function setLang(lang: Lang) {
  current = lang;
}

const LangContext = createContext<{ lang: Lang; change: (lang: Lang) => void }>({ lang: "it", change: () => undefined });

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setState] = useState<Lang>(current);
  const change = useCallback((next: Lang) => {
    current = next;
    try {
      window.localStorage.setItem(KEY, next);
    } catch {
      // Not remembered: fine for this visit.
    }
    setState(next);
  }, []);
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);
  const value = useMemo(() => ({ lang, change }), [lang, change]);
  return (
    <LangContext.Provider value={value}>
      {children}
    </LangContext.Provider>
  );
}

export const useLang = () => useContext(LangContext);
