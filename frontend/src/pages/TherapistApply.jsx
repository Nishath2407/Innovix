import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import Blobs from "../components/Blobs";
import api from "../services/api";
import { CONCERNS, LANGUAGES, SESSION_MODES } from "../constants";

const empty = {
  display_name: "", email: "", password: "", qualification: "", years_experience: "", session_price: "",
  gender: "", bio: "", approach: "", registration_number: "", issuing_body: "",
  specializations: [], languages: [], session_modes: [...SESSION_MODES.map((m) => m.value)],
};

function toggle(list, value) {
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
}

export default function TherapistApply() {
  const navigate = useNavigate();
  const [form, setForm] = useState(empty);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      await api.register({ ...form, role: "therapist", years_experience: Number(form.years_experience), session_price: Number(form.session_price) });
      setSuccess(true);
      setTimeout(() => navigate("/therapist/login"), 2200);
    } catch (err) {
      setError(err.payload?.message || "Something went wrong. Please check the form and try again.");
    } finally { setLoading(false); }
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs variant="quiet" />
      <Navbar />
      <div className="mx-auto max-w-2xl px-6 py-16">
        <h1 className="mb-2 font-display text-3xl font-extrabold">Apply as a therapist</h1>
        <p className="mb-8 text-ink-soft">Our team reviews every application before your profile goes live. This usually covers your registration/license details.</p>

        {success ? (
          <div className="glass rounded-4xl p-8 text-emerald-700 shadow-soft">Application received — we'll review your credentials before your profile goes live. Redirecting to the therapist login…</div>
        ) : (
          <form onSubmit={handleSubmit} className="glass flex flex-col gap-5 rounded-4xl p-8 shadow-glow">
            <div className="grid gap-4 sm:grid-cols-2">
              <input required placeholder="Full name (shown to clients)" value={form.display_name} onChange={(e) => set("display_name", e.target.value)} className="input" />
              <input required type="email" placeholder="Email" value={form.email} onChange={(e) => set("email", e.target.value)} className="input" />
              <input required type="password" placeholder="Password (8+ chars, incl. a number)" value={form.password} onChange={(e) => set("password", e.target.value)} className="input" />
              <select value={form.gender} onChange={(e) => set("gender", e.target.value)} className="input">
                <option value="">Gender (shown as a filter to clients)</option>
                <option value="female">Female</option><option value="male">Male</option><option value="non_binary">Non-binary</option>
              </select>
              <input required placeholder="Qualification (e.g. M.Phil Clinical Psychology)" value={form.qualification} onChange={(e) => set("qualification", e.target.value)} className="input sm:col-span-2" />
              <input required type="number" min="0" max="60" placeholder="Years of experience" value={form.years_experience} onChange={(e) => set("years_experience", e.target.value)} className="input" />
              <input required type="number" min="100" max="20000" placeholder="Session price (₹)" value={form.session_price} onChange={(e) => set("session_price", e.target.value)} className="input" />
              <input required placeholder="Registration / license number" value={form.registration_number} onChange={(e) => set("registration_number", e.target.value)} className="input" />
              <input required placeholder="Issuing body (e.g. RCI)" value={form.issuing_body} onChange={(e) => set("issuing_body", e.target.value)} className="input" />
            </div>

            <textarea placeholder="Short professional bio" rows={3} value={form.bio} onChange={(e) => set("bio", e.target.value)} className="input" />

            <div>
              <div className="mb-2 text-sm font-semibold text-ink-soft">Specializations</div>
              <div className="flex flex-wrap gap-2">
                {CONCERNS.map((c) => (
                  <button type="button" key={c.value} onClick={() => set("specializations", toggle(form.specializations, c.value))}
                    className={`rounded-full px-3 py-1.5 text-xs font-medium ${form.specializations.includes(c.value) ? "bg-lavender-deep text-white" : "bg-white/70 text-ink-soft"}`}>
                    {c.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <div className="mb-2 text-sm font-semibold text-ink-soft">Languages</div>
              <div className="flex flex-wrap gap-2">
                {LANGUAGES.map((l) => (
                  <button type="button" key={l.value} onClick={() => set("languages", toggle(form.languages, l.value))}
                    className={`rounded-full px-3 py-1.5 text-xs font-medium ${form.languages.includes(l.value) ? "bg-lavender-deep text-white" : "bg-white/70 text-ink-soft"}`}>
                    {l.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <div className="mb-2 text-sm font-semibold text-ink-soft">Session types you'll offer</div>
              <div className="flex flex-wrap gap-2">
                {SESSION_MODES.map((m) => (
                  <button type="button" key={m.value} onClick={() => set("session_modes", toggle(form.session_modes, m.value))}
                    className={`rounded-full px-3 py-1.5 text-xs font-medium ${form.session_modes.includes(m.value) ? "bg-lavender-deep text-white" : "bg-white/70 text-ink-soft"}`}>
                    {m.label}
                  </button>
                ))}
              </div>
            </div>

            {error && <div className="text-sm font-medium text-rose-600">{error}</div>}
            <button type="submit" disabled={loading} className="rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-400 py-3 text-sm font-semibold text-white shadow-soft disabled:opacity-60">
              {loading ? "Submitting…" : "Submit application"}
            </button>
          </form>
        )}
        <p className="mt-6 text-center text-xs text-ink-soft/70">Already approved? <Link to="/therapist/login" className="underline">Log in here</Link></p>
      </div>
      <style>{`.input { border-radius: 1rem; background: rgba(255,255,255,0.7); padding: 0.75rem 1rem; font-size: 0.875rem; outline: none; }`}</style>
    </div>
  );
}
