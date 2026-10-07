// frontend/src/CheckinPage.tsx
// The athlete-facing page. No accounts, no navigation, four taps per
// question, mobile first. Reached by a link the coach shared.
import { useEffect, useState } from "react";
import { CheckinPayload, Player } from "./types";
import { fetchPlayer, submitCheckin } from "./api";

type AnswerKey = "sleep" | "energy" | "soreness" | "stress";

const QUESTIONS: { key: AnswerKey; label: string; low: string; high: string }[] = [
  { key: "sleep", label: "How did you sleep?", low: "Very badly", high: "Very well" },
  { key: "energy", label: "How is your energy today?", low: "Empty", high: "Full of energy" },
  { key: "soreness", label: "How sore are your muscles?", low: "Very sore", high: "Not sore" },
  { key: "stress", label: "How stressed do you feel?", low: "Very stressed", high: "Very calm" },
];

const AREAS = [
  "Head",
  "Shoulder",
  "Chest or back",
  "Hip or groin",
  "Thigh",
  "Knee",
  "Ankle or foot",
  "Other",
];

export function CheckinPage({ playerId }: { playerId: string }) {
  const [player, setPlayer] = useState<Player | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<AnswerKey, number>>({
    sleep: 0,
    energy: 0,
    soreness: 0,
    stress: 0,
  });
  const [pain, setPain] = useState(false);
  const [painArea, setPainArea] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchPlayer(playerId)
      .then((p) => {
        if (!cancelled) setPlayer(p);
      })
      .catch(() => {
        if (!cancelled) setLoadError("This check-in link is not valid.");
      });
    return () => {
      cancelled = true;
    };
  }, [playerId]);

  const ready = QUESTIONS.every((q) => answers[q.key] > 0);

  const handleSubmit = async () => {
    if (!ready) {
      setSubmitError("Answer all four questions first.");
      return;
    }
    if (pain && !painArea) {
      setSubmitError("Tap where it hurts.");
      return;
    }
    setSubmitting(true);
    setSubmitError(null);
    const payload: CheckinPayload = {
      player_id: playerId,
      ...answers,
      pain,
      ...(pain ? { pain_area: painArea } : {}),
    };
    try {
      await submitCheckin(payload);
      setDone(true);
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : "Could not send the check-in.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (done) {
    return (
      <div className="checkin">
        <h1>Thank you</h1>
        <p>Your check-in reached your coach. You can close this page.</p>
      </div>
    );
  }
  if (loadError) {
    return (
      <div className="checkin">
        <h1>Link not valid</h1>
        <p>{loadError}</p>
      </div>
    );
  }
  return (
    <div className="checkin">
      <h1>Hi {player?.name ?? "there"}, check in for today</h1>
      <p className="checkin__sub">
        Takes under 20 seconds. Your coach sees the answers.
      </p>
      {QUESTIONS.map((q) => (
        <fieldset className="checkin__question" key={q.key}>
          <legend>{q.label}</legend>
          <div className="checkin__scale">
            {[1, 2, 3, 4, 5].map((value) => (
              <button
                type="button"
                key={value}
                className={
                  answers[q.key] === value
                    ? "checkin__pick is-chosen"
                    : "checkin__pick"
                }
                onClick={() =>
                  setAnswers((prev) => ({ ...prev, [q.key]: value }))
                }
              >
                {value}
              </button>
            ))}
          </div>
          <div className="checkin__ends">
            <span>{q.low}</span>
            <span>{q.high}</span>
          </div>
        </fieldset>
      ))}
      <fieldset className="checkin__question">
        <legend>Any pain today?</legend>
        <div className="checkin__scale">
          <button
            type="button"
            className={pain ? "checkin__pick" : "checkin__pick is-chosen"}
            onClick={() => setPain(false)}
          >
            No
          </button>
          <button
            type="button"
            className={pain ? "checkin__pick is-chosen" : "checkin__pick"}
            onClick={() => setPain(true)}
          >
            Yes
          </button>
        </div>
      </fieldset>
      {pain && (
        <fieldset className="checkin__question">
          <legend>Where does it hurt?</legend>
          <div className="checkin__areas">
            {AREAS.map((area) => (
              <button
                type="button"
                key={area}
                className={
                  painArea === area
                    ? "checkin__pick is-chosen"
                    : "checkin__pick"
                }
                onClick={() => setPainArea(area)}
              >
                {area}
              </button>
            ))}
          </div>
        </fieldset>
      )}
      <button
        type="button"
        className="checkin__submit"
        onClick={handleSubmit}
        disabled={!ready || submitting}
      >
        {submitting ? "Sending..." : "Send check-in"}
      </button>
      {submitError && <p className="checkin__error">{submitError}</p>}
    </div>
  );
}
