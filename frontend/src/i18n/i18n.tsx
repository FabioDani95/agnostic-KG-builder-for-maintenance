// The language of the interface. The Italian text is the key; the English dictionary gives its
// translation. Switching language remounts the screens, so every text is read again.
import { createContext, Fragment, type ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";
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
export function tr(text: string, values?: Record<string, string | number>): string {
  const translated = current === "en" ? (EN[text] ?? text) : text;
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
      <Fragment key={lang}>{children}</Fragment>
    </LangContext.Provider>
  );
}

export const useLang = () => useContext(LangContext);
