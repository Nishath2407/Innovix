import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import Blobs from "../components/Blobs";
import api from "../services/api";

const DAYS = [
  "Identify three things you can control today.",
  "Complete a short breathing exercise: in for 4, hold for 4, out for 6.",
  "Write down one thing you handled well recently.",
  "Reach out to someone you trust, even with a small message.",
  "Take a 10-minute walk without your phone.",
  "Write one kind thing about yourself.",
  "Reflect: what's one thing you'd like to carry forward?",
];

export default function Recovery() {
  const [state, setState] = useState(null);
  const [note, setNote] = useState("");

  const load = () => api.getRecovery().then(setState);
  useEffect(() => { load(); }, []);

  const complete = async (day) => {
    await api.completeRecoveryDay(day, note);
    setNote("");
    await load();
  };

  if (!state) return null;
  const nextDay = state.completed_days.length + 1;

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs variant="quiet" />
      <Navbar />
      <div className="mx-auto max-w-2xl px-6 py-14">
        <h1 className="mb-1 font-display text-3xl font-extrabold">7-day recovery journey</h1>
        <p className="mb-8 text-ink-soft">Small, optional steps — supportive wellness activities, not medical treatment.</p>

        <div className="mb-6 flex gap-2">
          {DAYS.map((_, i) => (
            <div key={i} className={`h-2 flex-1 rounded-full ${state.completed_days.includes(i + 1) ? "bg-gradient-to-r from-lavender-deep to-mint" : "bg-white/50"}`} />
          ))}
        </div>
        <div className="mb-6 text-sm font-semibold text-lavender-deep">🔥 {state.streak}-day streak</div>

        {nextDay <= 7 ? (
          <div className="glass rounded-4xl p-7 shadow-glow">
            <div className="mb-1 text-xs font-semibold text-ink-soft">Day {nextDay}</div>
            <p className="mb-4 font-display text-lg">{DAYS[nextDay - 1]}</p>
            <textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Optional reflection…" rows={2} className="mb-4 w-full rounded-2xl bg-white/70 px-4 py-2 text-sm outline-none" />
            <button onClick={() => complete(nextDay)} className="rounded-full bg-gradient-to-r from-lavender-deep to-lavender px-6 py-2.5 text-sm font-semibold text-white">Mark complete</button>
          </div>
        ) : (
          <div className="glass rounded-4xl p-7 text-center shadow-glow">
            <div className="mb-2 text-3xl">🎉</div>
            <p className="mb-4">You've completed the 7-day journey.</p>
            <button onClick={async () => { await api.resetRecovery(); load(); }} className="rounded-full bg-white/70 px-5 py-2.5 text-sm font-semibold">Start again</button>
          </div>
        )}
      </div>
    </div>
  );
}
