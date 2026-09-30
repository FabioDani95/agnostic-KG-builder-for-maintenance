import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { routes } from "./App";
import { LanguageProvider } from "./i18n/i18n";
import "./styles/tokens.css";
import "./styles/base.css";
import "./styles/components.css";
import "./styles/stage.css";
import "./styles/editor.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <LanguageProvider><RouterProvider router={createBrowserRouter(routes)} /></LanguageProvider>
  </StrictMode>,
);
