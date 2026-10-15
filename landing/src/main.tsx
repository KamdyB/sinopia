// landing/src/main.tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { LegalPage } from "./LegalPage";
import "./landing.css";

const path = window.location.pathname;
const legalKind = path === "/privacy" ? "privacy"
  : path === "/terms" ? "terms"
  : path === "/delete-account" ? "delete-account"
  : null;

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {legalKind ? <LegalPage kind={legalKind} /> : <App />}
  </StrictMode>,
);
