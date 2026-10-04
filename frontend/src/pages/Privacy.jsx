import Navbar from "../components/Navbar";
import Blobs from "../components/Blobs";

const ROWS = [
  ["Your identity to your therapist", "Anonymous display name, not your email"],
  ["Your journal", "Private — visible only to you"],
  ["AI check-in insights", "Private by default; you choose to share"],
  ["Your email", "Never shown to therapists by default"],
  ["Session data", "Encrypted in transit"],
];

export default function Privacy() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs variant="quiet" />
      <Navbar />
      <div className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="mb-4 font-display text-3xl font-extrabold">Privacy at SafeVoice</h1>
        <p className="mb-8 text-ink-soft">No exaggeration, no false claims of "complete anonymity."</p>
        <div className="glass mb-8 divide-y divide-line rounded-4xl shadow-soft">
          {ROWS.map(([label, value]) => (
            <div key={label} className="flex justify-between px-6 py-4 text-sm"><span className="text-ink-soft">{label}</span><span className="font-medium">{value}</span></div>
          ))}
        </div>
        <div className="glass rounded-4xl p-7 shadow-soft">
          <h2 className="mb-3 font-display text-lg font-bold">What we can't promise</h2>
          <p className="mb-3 text-ink-soft">SafeVoice is not completely untraceable. Account and payment records exist for legal and operational reasons. Quick Exit leaves sensitive screens instantly, but cannot clear your browser history, ISP logs, or employer/network monitoring.</p>
          <p className="text-ink-soft">AI-generated check-in insights are supportive, not diagnostic, and are never shared with your therapist unless you explicitly choose to.</p>
        </div>
      </div>
    </div>
  );
}
