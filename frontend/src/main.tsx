// frontend/src/main.tsx
import "./theme.css";
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { AuthGate } from "./AuthGate";
import { CheckinPage } from "./CheckinPage";
import { LegalRoute } from "./LegalRoute";
import { ThemeStage } from "./ThemeStage";

// Keep the athlete token in the URL fragment. Browsers do not send fragments
// to the server in HTTP requests or referrer headers, reducing access-log leakage.
const CHECKIN_PREFIX = "#checkin/";
const checkinToken = window.location.hash.startsWith(CHECKIN_PREFIX)
  ? window.location.hash.slice(CHECKIN_PREFIX.length)
  : null;

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    {checkinToken ? (
      <CheckinPage token={decodeURIComponent(checkinToken)} />
    ) : window.location.pathname === "/privacy" ? (
      <LegalRoute terms={false} />
    ) : window.location.pathname === "/terms" ? (
      <LegalRoute terms />
    ) : (
      <ThemeStage>
        <AuthGate>
          <App />
        </AuthGate>
      </ThemeStage>
    )}
  </React.StrictMode>,
);
