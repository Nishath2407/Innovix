import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import Blobs from "../components/Blobs";
import ExitSafelyButton from "../components/ExitSafelyButton";

const ITEMS = [
  ["Safety planning", "Build a private plan with trusted contacts and safe locations.", "/safety-plan"],
  ["Domestic violence support", "Curated, verified resources and next steps.", "/resources"],
  ["Workplace harassment", "Guidance on documentation, reporting, and support options.", "/resources"],
  ["Digital safety", "Practical steps to reduce exposure and protect your accounts.", "/resources"],
];

export default function Safety() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs />
      <Navbar />
      <div className="mx-auto max-w-4xl px-6 py-14">
        <h1 className="mb-3 font-display text-3xl font-extrabold">Women's Safety Hub</h1>
        <p className="mb-8 max-w-xl text-ink-soft">Specialized support when safety is part of the picture — with honest information about what it can and can't do. SafeVoice is not an emergency service; for immediate danger, contact local emergency services (112 in India).</p>
        <div className="grid gap-5 sm:grid-cols-2">
          {ITEMS.map(([title, desc, link]) => (
            <Link key={title} to={link} className="glass rounded-4xl p-6 shadow-soft transition hover:-translate-y-1">
              <h3 className="mb-2 font-display font-bold">{title}</h3>
              <p className="text-sm text-ink-soft">{desc}</p>
            </Link>
          ))}
        </div>
      </div>
      <ExitSafelyButton />
    </div>
  );
}
