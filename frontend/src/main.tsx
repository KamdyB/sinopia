import "./theme.css";
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { CheckinPage } from "./CheckinPage";
import { ThemeStage } from "./ThemeStage";

const path = window.location.pathname;
const checkinMatch = path.match(/^\/check-?in\/([^/]+)\/?$/);
const checkinId = checkinMatch ? decodeURIComponent(checkinMatch[1]) : null;
const isAuthRoute = ["/sign-in", "/sign-up", "/onboarding", "/privacy", "/terms"].includes(path);

function SimpleRoute() {
  if (isAuthRoute) {
    const legal = path === "/privacy" || path === "/terms";
    const title = path === "/sign-in" ? "Sign in to Sinopia" : path === "/sign-up" ? "Create your coach account" : path === "/onboarding" ? "Set up your team" : path === "/privacy" ? "Privacy" : "Terms";
    return <main className="page"><h1>{title}</h1><p>Coach accounts are not enabled yet. Please return when authentication is configured.</p><a href="/">Back to Sinopia</a></main>;
  }
  return <ThemeStage><App /></ThemeStage>;
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    {checkinId ? <CheckinPage playerId={checkinId} /> : <SimpleRoute />}
  </React.StrictMode>,
);
