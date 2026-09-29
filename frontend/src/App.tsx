import { lazy, Suspense } from "react";
import { Link, Route, Routes } from "react-router-dom";
import { TopBar } from "./components/Controls";
import { Library } from "./screens/Library";
import { ManualScreen } from "./screens/ManualScreen";
import { NewGraph } from "./screens/NewGraph";

// The graph screens carry three.js: they load only when opened.
const FinishedGraph = lazy(() => import("./screens/FinishedGraph").then((module) => ({ default: module.FinishedGraph })));
const LiveRun = lazy(() => import("./screens/LiveRun").then((module) => ({ default: module.LiveRun })));
const stage = (element: React.ReactNode) => <Suspense fallback={<div className="stage" />}>{element}</Suspense>;

function NotFound() {
  return (
    <div className="page">
      <TopBar />
      <main className="container">
        <div className="page-head">
          <h1 className="t-title">Pagina non trovata</h1>
        </div>
        <Link to="/">Torna ai grafi</Link>
      </main>
    </div>
  );
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Library />} />
      <Route path="/nuovo" element={<NewGraph />} />
      <Route path="/manuali/:manualId" element={<ManualScreen />} />
      <Route path="/manuali/:manualId/versioni/:versionId" element={stage(<FinishedGraph />)} />
      <Route path="/manuali/:manualId/versioni/:versionId/esecuzione" element={stage(<LiveRun />)} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
