import { useState } from "react";
import Navbar from "../components/Navbar";
import Blobs from "../components/Blobs";
import ExitSafelyButton from "../components/ExitSafelyButton";
import api from "../services/api";

export default function CheckIn() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    setLoading(true); setError(""); setResult(null);
    try { setResult(await api.checkIn(text)); }
    catch (err) { setError(err.status === 401 ? "Please log in to use the private check-in." : "Something went wrong. Please try again."); }
    finally { setLoading(false); }
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs variant="quiet" />
      <Navbar />
      <div className="mx-auto max-w-2xl px-6 py-16">
        <h1 className="mb-2 font-display text-3xl font-extrabold">Private check-in</h1>
        <p className="mb-8 text-ink-soft">Never diagnostic — here to help you prepare, not replace a professional.</p>
        <form onSubmit={submit} className="glass rounded-4xl p-7 shadow-glow">
          <textarea rows={4} value={text} onChange={(e) => setText(e.target.value)} placeholder="What are you currently going through?"
            className="w-full rounded-2xl bg-white/70 px-4 py-3 text-sm outline-none" />
          <button type="submit" disabled={loading} className="mt-4 rounded-full bg-gradient-to-r from-lavender-deep to-lavender px-6 py-3 text-sm font-semibold text-white disabled:opacity-60">
            {loading ? "Checking in…" : "Check in"}
          </button>
        </form>
        {error && <div className="mt-5 text-sm text-rose-600">{error}</div>}
        {result && (
          <div className="glass mt-6 rounded-4xl p-7 shadow-soft">
            <div className="mb-1 text-xs text-ink-soft">Primary emotion detected</div>
            <div className="mb-4 font-display text-xl font-bold capitalize text-lavender-deep">{result.primary_emotion}</div>
            <p className="mb-4 text-ink-soft">{result.message}</p>
            <div className="mb-3 rounded-2xl bg-white/60 p-4">
              <div className="font-display font-semibold text-lavender-deep">{result.risk.headline}</div>
              <div className="text-sm text-ink-soft">{result.risk.next_step}</div>
            </div>
            {result.emergency_note && <div className="mb-3 rounded-2xl bg-rose-50 p-4 text-sm text-rose-700">{result.emergency_note}</div>}
            <div className="text-xs text-ink-soft/70">{result.disclaimer}</div>
          </div>
        )}
      </div>
      <ExitSafelyButton />
    </div>
  );
}
