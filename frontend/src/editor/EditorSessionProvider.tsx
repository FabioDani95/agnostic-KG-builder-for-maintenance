import {
  createContext,
  useContext,
  useMemo,
  useReducer,
  type Dispatch,
  type ReactNode,
} from "react";
import type { EditorDocument } from "../api/types";
import {
  initialState,
  project,
  reducer,
  type Action,
  type EditorState,
} from "./reducer";
const Context = createContext<{
  state: EditorState;
  dispatch: Dispatch<Action>;
  graph: EditorDocument["graph"];
} | null>(null);
export function EditorSessionProvider({
  document,
  children,
}: {
  document: EditorDocument;
  children: ReactNode;
}) {
  const [state, dispatch] = useReducer(reducer, document, initialState);
  const graph = useMemo(
    () => state.preview?.graph ?? project(document.graph, state.operations),
    [document.graph, state.operations, state.preview],
  );
  return (
    <Context.Provider value={{ state, dispatch, graph }}>
      <div key={state.epoch} className="editor-session">
        {children}
      </div>
    </Context.Provider>
  );
}
export function useEditor() {
  const context = useContext(Context);
  if (!context) throw new Error("Editor session missing");
  return context;
}
