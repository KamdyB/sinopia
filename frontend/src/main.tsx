// frontend/src/main.tsx
import "./theme.css";
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { CheckinPage } from "./CheckinPage";
import { ThemeStage } from "./ThemeStage";

// Two entries in one bundle: the coach dashboard at any path, and the
// athlete check-in at /checkin/{player_id}. No router dependency needed.
const path = window.location.pathname;
const CHECKIN_PREFIX = "/checkin/";
const checkinId = path.startsWith(CHECKIN_PREFIX)
  ? path.slice(CHECKIN_PREFIX.length)
  : null;

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    {checkinId ? (
      <CheckinPage playerId={decodeURIComponent(checkinId)} />
    ) : (
      <ThemeStage>
        <App />
      </ThemeStage>
    )}
  </React.StrictMode>,
);
