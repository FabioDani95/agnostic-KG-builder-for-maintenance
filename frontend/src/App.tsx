import { lazy, Suspense } from "react";
import { Link, Outlet, type RouteObject } from "react-router-dom";
import { Shell } from "./components/Shell";
import { Guide } from "./screens/Guide";
import { Inbox } from "./screens/Inbox";
import { Library } from "./screens/Library";
import { ManualScreen } from "./screens/ManualScreen";
import { NewGraph } from "./screens/NewGraph";
import { OntologyScreen } from "./screens/OntologyScreen";
import { Questions } from "./screens/Questions";
import { Runs } from "./screens/Runs";
import { StatusProvider } from "./status/StatusProvider";
import { tr, useLang } from "./i18n/i18n";

// The graph screens carry three.js: they load only when opened.
const FinishedGraph = lazy(() => import("./screens/FinishedGraph").then((module) => ({ default: module.FinishedGraph })));
const EditorFlow = lazy(() => import("./editor/EditorFlow").then(module => ({ default: module.EditorFlow })));
const LiveRun = lazy(() => import("./screens/LiveRun").then((module) => ({ default: module.LiveRun })));
const stage = (element: React.ReactNode) => <Suspense fallback={<div className="stage" />}>{element}</Suspense>;

function NotFound() {
  return (
    <Shell title={tr("Pagina non trovata")}>
      <div className="empty">
        <p>{tr("Questa pagina non esiste: forse il collegamento è vecchio.")}</p>
        <Link to="/" className="button button-secondary">
          {tr("Torna ai grafi")}
        </Link>
      </div>
    </Shell>
  );
}

export function App() {
  useLang();
  return <StatusProvider><Outlet /></StatusProvider>;
}
export const routes: RouteObject[] = [{element: <App />, children: [
  {path: "/", element: <Library />},
  {path: "/nuovo", element: <NewGraph />},
  {path: "/tocca-a-te", element: <Inbox />},
  {path: "/esecuzioni", element: <Runs />},
  {path: "/ontologia", element: <OntologyScreen />},
  {path: "/guida", element: <Guide />},
  {path: "/guida/:chapter", element: <Guide />},
  {path: "/manuali/:manualId", element: <ManualScreen />},
  {path: "/manuali/:manualId/versioni/:versionId", element: stage(<FinishedGraph />)},
  {path: "/manuali/:manualId/versioni/:versionId/modifica", element: stage(<EditorFlow />)},
  {path: "/manuali/:manualId/versioni/:versionId/esecuzione", element: stage(<LiveRun />)},
  {path: "/manuali/:manualId/versioni/:versionId/domande", element: <Questions />},
  {path: "*", element: <NotFound />},
]}];
