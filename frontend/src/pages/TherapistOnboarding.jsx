import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";

const SPECIALIZATIONS = ["anxiety", "stress", "workplace_burnout", "relationships", "grief", "trauma", "womens_safety", "workplace_harassment", "self_confidence", "general_wellbeing"];
const LANGUAGES = [["en", "English"], ["hi", "Hindi"], ["te", "Telugu"]];

export default function TherapistOnboarding() {
  const { user } = useAuth();
  const [form, setForm] = useState({
    display_name: user?.display_name || "",
    qualification: "",
    years_experience: "",
    session_price: "",
    gender: "",
    bio: "",
    approach: "",
    specializations: [],
    languages: ["en"],
  });
  const [existing, setExisting] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api.getMyTherapistProfile()
      .then((data) => {
        if (data.therapist) {
          setExisting(data.therapist);
          setForm((f) => ({
            ...f,
            display_name: data.therapist.display_name,
            qualification: data.therapist.qualification,
            years_experience: data.therapist.years_experience,
            session_price: data.therapist.session_price,
            bio: data.therapist.bio || "",
            specializations: data.therapist.specializations || [],
            languages: data.therapist.languages || ["en"],
          }));
        }
      })
      .finally(() => setLoading(false));
  }, []);

  const toggleSpec = (spec) => {
    setForm((f) => ({
      ...f,
      specializations: f.specializations.includes(spec)
        ? f.specializations.filter((s) => s !== spec)
        : f.specializations.length < 6 ? [...f.specializations, spec] : f.specializations,
    }));
  };

  const toggleLang = (lang) => {
    setForm((f) => ({
      ...f,
      languages: f.languages.includes(lang) ? f.languages.filter((l) => l !== lang) : [...f.languages, lang],
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");
    try {
      const data = await api.saveMyTherapistProfile(form);
      setExisting(data.therapist);
      setMessage(data.message);
    } catch (err) {
      setError(err.payload?.fields ? Object.values(err.payload.fields)[0] : err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div>
        <Navbar />
        <div className="mx-auto max-w-2xl px-6 py-24 text-text-muted">Loading your profile...</div>
      </div>
    );
  }

  return (
    <div>
      <Navbar />
      <div className="mx-auto max-w-2xl px-6 py-16">
        <h1 className="mb-2 font-serif text-3xl font-bold">Your therapist profile</h1>
        <p className="mb-8 text-text-muted">
          {existing
            ? existing.is_verified
              ? "Your profile is live and visible to clients. Editing it will send it back for review."
              : "Your profile is saved and waiting for admin verification — it isn't publicly visible yet."
            : "Fill this in to create your public profile. An admin reviews it before it appears in search."}
        </p>

        {existing && (
          <div className={`mb-6 rounded-xl border p-4 text-sm ${existing.is_verified ? "border-mint/30 bg-mint/5 text-mint" : "border-line bg-surface-2 text-text-muted"}`}>
            Status: {existing.is_verified ? "Verified — live in search" : "Pending admin verification"}
          </div>
        )}

        <form onSubmit={handleSubmit} className="glass flex flex-col gap-4 rounded-2xl p-6">
          <input
            placeholder="Display name (shown to clients)" value={form.display_name}
            onChange={(e) => setForm({ ...form, display_name: e.target.value })}
            className="rounded-lg border border-line bg-white px-4 py-3 outline-none focus:border-accent"
          />
          <input
            placeholder="Qualification (e.g. M.A. Clinical Psychology)" value={form.qualification}
            onChange={(e) => setForm({ ...form, qualification: e.target.value })}
            className="rounded-lg border border-line bg-white px-4 py-3 outline-none focus:border-accent"
          />
          <div className="grid grid-cols-2 gap-4">
            <input
              type="number" min="0" placeholder="Years of experience" value={form.years_experience}
              onChange={(e) => setForm({ ...form, years_experience: e.target.value })}
              className="rounded-lg border border-line bg-white px-4 py-3 outline-none focus:border-accent"
            />
            <input
              type="number" min="0" placeholder="Session price (₹)" value={form.session_price}
              onChange={(e) => setForm({ ...form, session_price: e.target.value })}
              className="rounded-lg border border-line bg-white px-4 py-3 outline-none focus:border-accent"
            />
          </div>
          <textarea
            rows={3} placeholder="Short bio" value={form.bio}
            onChange={(e) => setForm({ ...form, bio: e.target.value })}
            className="rounded-lg border border-line bg-white px-4 py-3 outline-none focus:border-accent"
          />

          <div>
            <div className="mb-2 text-sm text-text-muted">Specializations (up to 6)</div>
            <div className="flex flex-wrap gap-2">
              {SPECIALIZATIONS.map((s) => (
                <button
                  type="button" key={s} onClick={() => toggleSpec(s)}
                  className={`rounded-full border px-3 py-1.5 text-xs capitalize ${
                    form.specializations.includes(s) ? "border-accent bg-accent/10 text-accent-bright" : "border-line text-text-muted"
                  }`}
                >
                  {s.replace("_", " ")}
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="mb-2 text-sm text-text-muted">Languages</div>
            <div className="flex flex-wrap gap-2">
              {LANGUAGES.map(([code, label]) => (
                <button
                  type="button" key={code} onClick={() => toggleLang(code)}
                  className={`rounded-full border px-3 py-1.5 text-xs ${
                    form.languages.includes(code) ? "border-accent bg-accent/10 text-accent-bright" : "border-line text-text-muted"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {error && <div className="text-sm text-red-500">{error}</div>}
          {message && <div className="text-sm text-mint">{message}</div>}

          <button
            type="submit" disabled={saving}
            className="mt-2 self-start rounded-full bg-gold px-6 py-3 font-medium text-white disabled:opacity-60"
          >
            {saving ? "Saving..." : existing ? "Update profile" : "Create profile"}
          </button>
        </form>
      </div>
    </div>
  );
}
