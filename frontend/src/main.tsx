import "./theme.css";
import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { AuthPage } from "./AuthPage";
import { CheckinPage } from "./CheckinPage";
import { OnboardingPage } from "./OnboardingPage";
import { ThemeStage } from "./ThemeStage";

const path = window.location.pathname;
const API_BASE = (import.meta.env.VITE_API_BASE || "/api").replace(/\/+$/, "");
const checkinMatch = path.match(/^\/check-?in\/([^/]+)\/?$/);
const checkinToken = checkinMatch ? decodeURIComponent(checkinMatch[1]) : null;
const authRoutes = ["/sign-in", "/sign-up"];
const appRoutes = ["/app", "/app/athletes", "/app/sessions"];

function RootRedirect() {
  useEffect(() => {
    fetch(`${API_BASE}/auth/me`, { credentials: "include" })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("signed-out")))
      .then((body) => window.location.replace(body.team ? "/app" : "/onboarding"))
      .catch(() => window.location.replace("/sign-in"));
  }, []);
  return <main className="page"><p>Opening Sinopia…</p></main>;
}

function ProtectedApp() {
  const [teamType, setTeamType] = useState<"girls" | "boys" | "mixed" | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    fetch(`${API_BASE}/auth/me`, { credentials: "include" })
      .then(async (response) => {
        const body = await response.json().catch(() => ({}));
        if (response.status === 401) { window.location.replace("/sign-in?expired=1"); return; }
        if (!response.ok) throw new Error(body.detail || "Could not load your account.");
        if (!body.team) { window.location.replace("/onboarding"); return; }
        if (active) setTeamType(body.team.team_type);
      })
      .catch((e) => { if (active) setError(e instanceof Error ? e.message : "Could not load your account."); });
    return () => { active = false; };
  }, []);
  if (error) return <main className="page"><h1>Sinopia could not load</h1><p role="alert">{error}</p><button onClick={() => window.location.reload()}>Try again</button></main>;
  if (!teamType) return <main className="page"><p>Loading your team…</p></main>;
  return <ThemeStage><App initialTeamType={teamType} /></ThemeStage>;
}

function LegalPage({ terms }: { terms: boolean }) {
  return <main className="page"><section className="panel">
    <h1>{terms ? "Terms" : "Privacy"}</h1>
    {terms ? <>
      <p>Sinopia is a workload-monitoring aid, not medical advice, diagnosis, or injury prediction. Coaches remain responsible for decisions and should refer health concerns to qualified professionals.</p>
      <p>Use accurate information, protect athlete check-in links, and do not use the tool to rank, scout, or punish young athletes.</p>
    </> : <>
      <p>Sinopia collects training and wellbeing information entered by a coach or athlete so the coach can review workload and check-ins.</p>
      <p>Athlete check-ins are shared with the coach responsible for that team. Sinopia is not a medical service and its flags are not diagnoses.</p>
      <p>Do not enter information you are not comfortable sharing. For questions about stored data, contact the coach who gave you the link.</p>
    </>}
    <p><a href="/sign-in">Back to Sinopia</a></p>
  </section></main>;
}

function Router() {
  if (checkinToken) return <CheckinPage playerId={checkinToken} />;
  if (path === "/") return <RootRedirect />;
  if (path === "/sign-in" || path === "/sign-up") return <AuthPage intent={path === "/sign-up" ? "sign-up" : "sign-in"} />;
  if (path === "/onboarding") return <OnboardingPage />;
  if (path === "/privacy") return <LegalPage terms={false} />;
  if (path === "/terms") return <LegalPage terms />;
  if (appRoutes.includes(path)) return <ProtectedApp />;
  return <RootRedirect />;
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode><Router /></React.StrictMode>,
);
