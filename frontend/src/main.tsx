import "./theme.css";
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { CheckinPage } from "./CheckinPage";
import { ThemeStage } from "./ThemeStage";

const path = window.location.pathname;
if (path === "/") window.location.replace("/sign-in");
const checkinMatch = path.match(/^\/check-?in\/([^/]+)\/?$/);
const checkinId = checkinMatch ? decodeURIComponent(checkinMatch[1]) : null;
const isAuthRoute = ["/sign-in", "/sign-up", "/onboarding", "/privacy", "/terms"].includes(path);

function SimpleRoute() {
  if (isAuthRoute) {
    const title = path === "/sign-in" ? "Sign in to Sinopia" : path === "/sign-up" ? "Create your coach account" : path === "/onboarding" ? "Set up your team" : path === "/privacy" ? "Privacy" : "Terms";
    if (path === "/privacy") return <main className="page"><h1>Privacy</h1><p>Sinopia collects training and wellbeing information entered by a coach or athlete so the coach can review workload and check-ins.</p><p>Athlete check-ins are shared with the coach responsible for that team. Sinopia is not a medical service and its flags are not diagnoses.</p><p>Do not enter information you are not comfortable sharing. For questions about stored data, contact the coach who gave you the link.</p><a href="/sign-in">Back to Sinopia</a></main>;
    if (path === "/terms") return <main className="page"><h1>Terms</h1><p>Sinopia is a workload-monitoring aid, not medical advice, diagnosis, or injury prediction. Coaches remain responsible for decisions and should refer health concerns to qualified professionals.</p><p>Use accurate information, protect athlete check-in links, and do not use the tool to rank, scout, or punish young athletes.</p><a href="/sign-in">Back to Sinopia</a></main>;
    return <main className="page"><h1>{title}</h1><p>Coach account authentication is being configured. Athlete check-in links remain available without an account.</p><a href="/privacy">Privacy</a> · <a href="/terms">Terms</a></main>;
  }
  return <ThemeStage><App /></ThemeStage>;
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    {checkinId ? <CheckinPage playerId={checkinId} /> : <SimpleRoute />}
  </React.StrictMode>,
);
