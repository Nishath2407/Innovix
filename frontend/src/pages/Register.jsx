import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";
import Blobs from "../components/Blobs";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "", display_name: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      await register(form);
      setSuccess(true);
      setTimeout(() => navigate("/login"), 1600);
    } catch (err) {
      setError(err.payload?.fields ? Object.values(err.payload.fields)[0] : err.message);
    } finally { setLoading(false); }
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs />
      <Navbar />
      <div className="mx-auto flex max-w-md flex-col px-6 py-20">
        <div className="glass rounded-4xl p-8 shadow-glow">
          <h1 className="mb-1 font-display text-2xl font-extrabold">Create your account</h1>
          <p className="mb-7 text-sm text-ink-soft">Your email is only for login — your therapist never sees it.</p>
          {success ? (
            <div className="rounded-2xl bg-emerald-50 p-5 text-emerald-700">Account created. Redirecting to login…</div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
              <input name="display_name" placeholder="Display name (optional)" value={form.display_name} onChange={handleChange}
                className="rounded-2xl bg-white/70 px-4 py-3 text-sm outline-none ring-1 ring-transparent focus:ring-lavender" />
              <input name="email" type="email" required placeholder="Email" value={form.email} onChange={handleChange}
                className="rounded-2xl bg-white/70 px-4 py-3 text-sm outline-none ring-1 ring-transparent focus:ring-lavender" />
              <input name="password" type="password" required placeholder="Password (8+ chars, incl. a number)" value={form.password} onChange={handleChange}
                className="rounded-2xl bg-white/70 px-4 py-3 text-sm outline-none ring-1 ring-transparent focus:ring-lavender" />
              {error && <div className="text-sm font-medium text-rose-600">{error}</div>}
              <button type="submit" disabled={loading}
                className="mt-1 rounded-2xl bg-gradient-to-r from-lavender-deep to-lavender py-3 text-sm font-semibold text-white shadow-soft disabled:opacity-60">
                {loading ? "Creating account…" : "Create account"}
              </button>
            </form>
          )}
          <div className="mt-6 text-sm text-ink-soft">
            Already have an account? <Link to="/login" className="font-medium text-lavender-deep">Log in</Link>
          </div>
        </div>
        <p className="mt-6 text-center text-xs text-ink-soft/70">
          Are you a therapist? <Link to="/therapist/apply" className="underline">Apply here</Link>
        </p>
      </div>
    </div>
  );
}
