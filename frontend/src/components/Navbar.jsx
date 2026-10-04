import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const roleHome = { user: "/dashboard", therapist: "/therapist/dashboard", admin: "/admin/dashboard" };

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-40 px-4 pt-4">
      <nav className="glass mx-auto flex h-16 max-w-6xl items-center justify-between rounded-full px-6 shadow-soft">
        <Link to="/" className="flex items-center gap-2 font-display text-lg font-extrabold text-ink">
          <span className="grid h-8 w-8 place-items-center rounded-full bg-gradient-to-br from-lavender to-mint text-white">✦</span>
          SafeVoice
        </Link>
        <div className="hidden gap-7 text-sm font-medium text-ink-soft md:flex">
          <Link to="/therapists" className="hover:text-lavender-deep">Therapists</Link>
          <Link to="/match" className="hover:text-lavender-deep">Find my match</Link>
          <Link to="/safety" className="hover:text-lavender-deep">Safety hub</Link>
          <Link to="/privacy" className="hover:text-lavender-deep">Privacy</Link>
        </div>
        <div className="flex items-center gap-2">
          {user ? (
            <>
              <Link to={roleHome[user.role] || "/dashboard"} className="rounded-full px-4 py-2 text-sm font-medium text-ink-soft hover:bg-white/70">Dashboard</Link>
              <button onClick={logout} className="rounded-full bg-ink px-4 py-2 text-sm font-semibold text-white hover:bg-ink/90">Log out</button>
            </>
          ) : (
            <>
              <Link to="/login" className="rounded-full px-4 py-2 text-sm font-medium text-ink-soft hover:bg-white/70">Log in</Link>
              <Link to="/register" className="rounded-full bg-gradient-to-r from-lavender-deep to-lavender px-5 py-2 text-sm font-semibold text-white shadow-soft hover:opacity-90">Get started</Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
