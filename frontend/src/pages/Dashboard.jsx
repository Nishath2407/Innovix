import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import Blobs from "../components/Blobs";
import ExitSafelyButton from "../components/ExitSafelyButton";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";

const CARDS = [
  ["/therapists", "Find a therapist", "🧑‍⚕️", "Browse licensed professionals matched to your needs."],
  ["/match", "Smart match", "✨", "Answer a few questions for a transparent recommendation."],
  ["/check-in", "Private check-in", "💬", "A quiet space to name what you're feeling."],
  ["/journal", "Journal", "📔", "Private notes only you can see."],
  ["/appointments", "Appointments", "📅", "Manage your upcoming and past sessions."],
  ["/progress", "Progress", "📈", "See your mood trends over time."],
  ["/recovery", "Recovery", "🌱", "A 7-day starter journey of small steps."],
  ["/safety-plan", "Safety plan", "🛡️", "Build a private plan with trusted contacts."],
];

export default function Dashboard() {
  const { user } = useAuth();
  const [next, setNext] = useState(null);

  useEffect(() => {
    api.listAppointments().then((d) => {
      const upcoming = d.appointments.filter((a) => a.status === "confirmed").sort((a, b) => a.scheduled_start.localeCompare(b.scheduled_start));
      setNext(upcoming[0] || null);
    }).catch(() => {});
  }, []);

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs />
      <Navbar />
      <div className="mx-auto max-w-6xl px-6 py-14">
        <h1 className="mb-1 font-display text-3xl font-extrabold">Welcome back{user?.display_name ? `, ${user.display_name}` : ""}.</h1>
        <p className="mb-8 text-ink-soft">Here's where you left off.</p>

        {next && (
          <div className="glass mb-8 flex items-center justify-between rounded-4xl p-6 shadow-glow">
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-lavender-deep">Next session</div>
              <div className="font-display text-lg font-bold">{next.therapist_name} · {new Date(next.scheduled_start).toLocaleString([], { weekday: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</div>
            </div>
            <Link to="/appointments" className="rounded-full bg-ink px-5 py-2.5 text-sm font-semibold text-white">View</Link>
          </div>
        )}

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {CARDS.map(([href, title, icon, desc]) => (
            <Link key={href} to={href} className="glass rounded-4xl p-6 shadow-soft transition hover:-translate-y-1">
              <div className="mb-3 text-2xl">{icon}</div>
              <h3 className="mb-1 font-display font-bold">{title}</h3>
              <p className="text-xs text-ink-soft">{desc}</p>
            </Link>
          ))}
        </div>
      </div>
      <ExitSafelyButton />
    </div>
  );
}
