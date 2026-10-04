import { useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import Blobs from "../components/Blobs";
import api from "../services/api";
import { CONCERNS, LANGUAGES } from "../constants";

export default function Match() {
  const [prefs, setPrefs] = useState({ concern: "", language: "", mode: "", gender: "any", time: "any", budget: "", urgency: "" });
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      const payload = { ...prefs, budget: prefs.budget ? Number(prefs.budget) : null };
      setResults(await api.match(payload));
    } finally { setLoading(false); }
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs />
      <Navbar />
      <div className="mx-auto max-w-2xl px-6 py-14">
        <h1 className="mb-2 font-display text-3xl font-extrabold">Find my match</h1>
        <p className="mb-8 text-ink-soft">A few quick questions for a transparent recommendation — not a clinical one.</p>

        <div className="glass flex flex-col gap-5 rounded-4xl p-7 shadow-glow">
          <Field label="What are you looking for support with?">
            <Chips options={CONCERNS} value={prefs.concern} onChange={(v) => setPrefs({ ...prefs, concern: v })} />
          </Field>
          <Field label="Preferred language">
            <Chips options={LANGUAGES} value={prefs.language} onChange={(v) => setPrefs({ ...prefs, language: v })} />
          </Field>
          <Field label="How would you like to talk?">
            <Chips options={[{ value: "video", label: "Video" }, { value: "audio", label: "Audio" }, { value: "text", label: "Text" }]} value={prefs.mode} onChange={(v) => setPrefs({ ...prefs, mode: v })} />
          </Field>
          <Field label="Therapist gender preference">
            <Chips options={[{ value: "any", label: "No preference" }, { value: "female", label: "Female" }, { value: "male", label: "Male" }]} value={prefs.gender} onChange={(v) => setPrefs({ ...prefs, gender: v })} />
          </Field>
          <Field label="Preferred time">
            <Chips options={[{ value: "any", label: "Any" }, { value: "morning", label: "Morning" }, { value: "afternoon", label: "Afternoon" }, { value: "evening", label: "Evening" }]} value={prefs.time} onChange={(v) => setPrefs({ ...prefs, time: v })} />
          </Field>
          <Field label="Budget (₹ per session)">
            <input type="number" value={prefs.budget} onChange={(e) => setPrefs({ ...prefs, budget: e.target.value })} placeholder="e.g. 1500" className="w-40 rounded-2xl bg-white/70 px-4 py-2 text-sm outline-none" />
          </Field>
          <Field label="Urgency">
            <Chips options={[{ value: "", label: "No rush" }, { value: "soon", label: "As soon as possible" }]} value={prefs.urgency} onChange={(v) => setPrefs({ ...prefs, urgency: v })} />
          </Field>
          <button onClick={submit} disabled={loading} className="rounded-full bg-gradient-to-r from-lavender-deep to-lavender py-3 text-sm font-semibold text-white disabled:opacity-60">
            {loading ? "Matching…" : "Show my matches"}
          </button>
        </div>

        {results && (
          <div className="mt-8">
            <p className="mb-4 text-xs text-ink-soft/70">{results.disclaimer}</p>
            <div className="flex flex-col gap-4">
              {results.matches.map((m) => (
                <div key={m.therapist.id} className="glass rounded-4xl p-6 shadow-soft">
                  <div className="mb-2 flex items-center justify-between">
                    <div className="font-display font-bold">{m.therapist.display_name}</div>
                    <div className="rounded-full bg-lavender-deep px-3 py-1 text-xs font-bold text-white">{m.score}% match</div>
                  </div>
                  <ul className="mb-3 list-inside list-disc text-sm text-ink-soft">
                    {m.reasons.map((r) => <li key={r}>{r}</li>)}
                  </ul>
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-semibold">₹{m.therapist.session_price}</span>
                    <Link to="/therapists" className="rounded-full bg-ink px-4 py-2 text-xs font-semibold text-white">View & book</Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return <div><div className="mb-2 text-sm font-semibold text-ink-soft">{label}</div>{children}</div>;
}
function Chips({ options, value, onChange }) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((o) => (
        <button key={o.value} type="button" onClick={() => onChange(o.value)} className={`rounded-full px-3 py-1.5 text-xs font-medium ${value === o.value ? "bg-lavender-deep text-white" : "bg-white/70 text-ink-soft"}`}>
          {o.label}
        </button>
      ))}
    </div>
  );
}
