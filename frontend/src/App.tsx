import { lazy, Suspense } from "react";
import { Link, Route, Routes } from "react-router-dom";
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
import { tr } from "./i18n/i18n";

// The graph screens carry three.js: they load only when opened.
const FinishedGraph = lazy(() => import("./screens/FinishedGraph").then((module) => ({ default: module.FinishedGraph })));
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
  return (
    <StatusProvider>
      <Routes>
        <Route path="/" element={<Library />} />
        <Route path="/nuovo" element={<NewGraph />} />
        <Route path="/tocca-a-te" element={<Inbox />} />
        <Route path="/esecuzioni" element={<Runs />} />
        <Route path="/ontologia" element={<OntologyScreen />} />
        <Route path="/guida" element={<Guide />} />
        <Route path="/guida/:chapter" element={<Guide />} />
        <Route path="/manuali/:manualId" element={<ManualScreen />} />
        <Route path="/manuali/:manualId/versioni/:versionId" element={stage(<FinishedGraph />)} />
        <Route path="/manuali/:manualId/versioni/:versionId/esecuzione" element={stage(<LiveRun />)} />
        <Route path="/manuali/:manualId/versioni/:versionId/domande" element={<Questions />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </StatusProvider>
  );
}
