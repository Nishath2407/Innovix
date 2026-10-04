import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";
import Blobs from "../components/Blobs";

const CONFIG = {
  user: { title: "Welcome back", sub: "Log in to continue your care.", redirect: "/dashboard", registerLink: "/register", registerLabel: "Create an account", accent: "from-lavender-deep to-lavender" },
  therapist: { title: "Therapist login", sub: "Access your appointments, clients, and schedule.", redirect: "/therapist/dashboard", registerLink: "/therapist/apply", registerLabel: "Apply as a therapist", accent: "from-emerald-500 to-teal-400" },
  admin: { title: "Admin login", sub: "Platform oversight and monitoring.", redirect: "/admin/dashboard", registerLink: null, registerLabel: null, accent: "from-ink to-ink-soft" },
};

export default function Login({ portal = "user" }) {
  const cfg = CONFIG[portal];
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      await login(email, password, portal);
      navigate(cfg.redirect);
    } catch (err) {
      setError(err.payload?.message || "Incorrect email or password.");
    } finally { setLoading(false); }
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs variant="quiet" />
      <Navbar />
      <div className="mx-auto flex max-w-md flex-col px-6 py-20">
        <div className="glass rounded-4xl p-8 shadow-glow">
          <h1 className="mb-1 font-display text-2xl font-extrabold">{cfg.title}</h1>
          <p className="mb-7 text-sm text-ink-soft">{cfg.sub}</p>
          <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
            <input type="email" required placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)}
              className="rounded-2xl bg-white/70 px-4 py-3 text-sm outline-none ring-1 ring-transparent focus:ring-lavender" />
            <input type="password" required placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)}
              className="rounded-2xl bg-white/70 px-4 py-3 text-sm outline-none ring-1 ring-transparent focus:ring-lavender" />
            {error && <div className="text-sm font-medium text-rose-600">{error}</div>}
            <button type="submit" disabled={loading}
              className={`mt-1 rounded-2xl bg-gradient-to-r ${cfg.accent} py-3 text-sm font-semibold text-white shadow-soft disabled:opacity-60`}>
              {loading ? "Logging in…" : "Log in"}
            </button>
          </form>
          <div className="mt-6 flex justify-between text-sm text-ink-soft">
            <Link to="/forgot-password" className="hover:text-ink">Forgot password?</Link>
            {cfg.registerLink && <Link to={cfg.registerLink} className="hover:text-ink">{cfg.registerLabel}</Link>}
          </div>
        </div>
        {portal === "user" && (
          <p className="mt-6 text-center text-xs text-ink-soft/70">
            Therapist? <Link to="/therapist/login" className="underline">Log in here</Link> · Admin? <Link to="/admin/login" className="underline">Log in here</Link>
          </p>
        )}
      </div>
    </div>
  );
}
