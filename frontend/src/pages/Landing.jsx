import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import Blobs from "../components/Blobs";
import ExitSafelyButton from "../components/ExitSafelyButton";

const MODES = {
  video: { label: "Video", desc: "Face-to-face when you want the closest thing to being in the room together.", emoji: "🎥" },
  audio: { label: "Audio", desc: "All the presence of a real conversation, none of the camera pressure.", emoji: "🎧" },
  text: { label: "Text", desc: "Real-time typed sessions — often easier for saying the harder things first.", emoji: "💬" },
};

export default function Landing() {
  const [mode, setMode] = useState("video");
  const [checkText, setCheckText] = useState("");
  const [checkResp, setCheckResp] = useState(null);
  const [testiIndex, setTestiIndex] = useState(0);

  const testimonials = [
    { quote: "I liked that I could do my first session over text. Starting was the hardest part.", meta: "IT professional" },
    { quote: "Knowing my therapist couldn't just see my email made it easier to actually be honest.", meta: "Graduate student" },
    { quote: "The matching explained itself — I understood exactly why I was paired with my therapist.", meta: "Working professional" },
  ];

  useEffect(() => {
    const t = setInterval(() => setTestiIndex((i) => (i + 1) % testimonials.length), 6000);
    return () => clearInterval(t);
  }, []);

  const runDemo = () => {
    if (!checkText.trim()) return;
    setCheckResp("...");
    const t = checkText.toLowerCase();
    setTimeout(() => {
      if (/dread|edge|anxious|anxiety|nervous/.test(t)) setCheckResp("Your message shows signs of anxiety. A therapist matched to workplace stress could be a good starting point.");
      else if (/low|unmotivated|sad|down|empty/.test(t)) setCheckResp("Your message shows signs of low mood. A conversation with someone trained to help often makes more difference than it seems right now.");
      else if (/argument|relationship|partner|fight/.test(t)) setCheckResp("Your message shows signs of relationship stress. A relationship-focused therapist could help you unpack this.");
      else setCheckResp("Thanks for sharing — a therapist specializing in general wellbeing could be a good place to start.");
    }, 500);
  };

  return (
    <div className="relative overflow-hidden">
      <Blobs />
      <Navbar />

      {/* Hero */}
      <section className="relative px-4 pb-20 pt-14">
        <div className="mx-auto grid max-w-6xl items-center gap-14 md:grid-cols-[1.1fr_0.9fr]">
          <div>
            <div className="mb-5 inline-flex items-center gap-2 rounded-full bg-white/70 px-4 py-1.5 text-xs font-semibold text-lavender-deep shadow-soft">
              ✦ Private online mental-health support
            </div>
            <h1 className="mb-5 font-display text-5xl font-extrabold leading-[1.08] text-ink sm:text-6xl">
              Professional support,<br />wherever you are.
            </h1>
            <p className="mb-8 max-w-md text-lg text-ink-soft">
              Connect with licensed therapists through private online sessions that fit your time, your comfort, and how you'd rather talk.
            </p>
            <div className="mb-6 flex flex-wrap gap-3">
              <Link to="/therapists" className="rounded-full bg-gradient-to-r from-lavender-deep to-lavender px-7 py-3.5 font-semibold text-white shadow-glow transition hover:scale-[1.03]">
                Find a Therapist
              </Link>
              <Link to="/check-in" className="rounded-full bg-white/80 px-7 py-3.5 font-semibold text-ink shadow-soft transition hover:scale-[1.03]">
                Try the check-in ↓
              </Link>
            </div>
            <p className="text-sm text-ink-soft/80">Your therapist never sees your email by default.</p>
          </div>

          {/* interactive mode switcher */}
          <div className="glass rounded-4xl p-3 shadow-glow">
            <div className="flex gap-2 rounded-3xl bg-white/50 p-1.5">
              {Object.entries(MODES).map(([key, m]) => (
                <button key={key} onClick={() => setMode(key)}
                  className={`flex-1 rounded-2xl py-2.5 text-sm font-semibold transition ${mode === key ? "bg-white text-lavender-deep shadow" : "text-ink-soft"}`}>
                  {m.emoji} {m.label}
                </button>
              ))}
            </div>
            <div className="flex flex-col items-center px-6 py-10 text-center">
              <div className="mb-4 text-5xl">{MODES[mode].emoji}</div>
              <h3 className="mb-2 font-display text-xl font-bold">{MODES[mode].label} sessions</h3>
              <p className="max-w-[28ch] text-sm text-ink-soft">{MODES[mode].desc}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Why - bento grid */}
      <section className="relative px-4 py-16">
        <div className="mx-auto max-w-6xl">
          <h2 className="mb-10 text-center font-display text-3xl font-extrabold">Made for how you actually live</h2>
          <div className="grid gap-5 md:grid-cols-3">
            {[
              ["🛋️", "No commute, no waiting room", "Sessions happen wherever you have a quiet moment."],
              ["🗣️", "Talk your way", "Video isn't required — audio and text work too."],
              ["🔒", "Privacy by design", "Your therapist sees what's relevant, not your inbox."],
            ].map(([icon, title, desc]) => (
              <div key={title} className="glass rounded-4xl p-7 shadow-soft transition hover:-translate-y-1">
                <div className="mb-4 text-3xl">{icon}</div>
                <h3 className="mb-2 font-display text-lg font-bold">{title}</h3>
                <p className="text-sm text-ink-soft">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AI check-in live demo */}
      <section className="relative px-4 py-16">
        <div className="mx-auto max-w-2xl">
          <h2 className="mb-3 text-center font-display text-3xl font-extrabold">Try the private check-in</h2>
          <p className="mb-8 text-center text-ink-soft">Type how you're feeling — this is a live preview, not a diagnosis.</p>
          <div className="glass rounded-4xl p-7 shadow-glow">
            <div className="mb-4 flex gap-2 overflow-x-auto">
              {["I've been dreading Monday all weekend.", "I can't stop thinking about our argument.", "I just feel low and unmotivated."].map((s) => (
                <button key={s} onClick={() => { setCheckText(s); }} className="whitespace-nowrap rounded-full bg-white/70 px-3 py-1.5 text-xs font-medium text-ink-soft hover:bg-white">
                  {s.slice(0, 24)}…
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <input value={checkText} onChange={(e) => setCheckText(e.target.value)} placeholder="What are you currently going through?"
                className="flex-1 rounded-2xl border-none bg-white/70 px-4 py-3 text-sm outline-none ring-1 ring-transparent focus:ring-lavender" />
              <button onClick={runDemo} className="rounded-2xl bg-ink px-5 py-3 text-sm font-semibold text-white">Check in</button>
            </div>
            {checkResp && <div className="mt-5 rounded-2xl bg-white/60 p-4 text-sm text-ink">{checkResp}</div>}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="relative px-4 py-16">
        <div className="mx-auto max-w-xl text-center">
          <div className="glass min-h-[140px] rounded-4xl p-8 shadow-soft">
            <p className="font-display text-xl font-medium italic">"{testimonials[testiIndex].quote}"</p>
            <p className="mt-4 text-sm text-ink-soft">{testimonials[testiIndex].meta}</p>
          </div>
          <div className="mt-4 flex justify-center gap-2">
            {testimonials.map((_, i) => (
              <button key={i} onClick={() => setTestiIndex(i)} className={`h-2 rounded-full transition-all ${i === testiIndex ? "w-6 bg-lavender-deep" : "w-2 bg-ink-soft/30"}`} />
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="relative px-4 py-20">
        <div className="glass mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-8 rounded-5xl p-12 shadow-glow">
          <div>
            <h2 className="mb-2 font-display text-3xl font-extrabold">Ready when you are.</h2>
            <p className="text-ink-soft">Start with a free check-in, or go straight to browsing therapists.</p>
          </div>
          <Link to="/therapists" className="rounded-full bg-gradient-to-r from-lavender-deep to-lavender px-7 py-3.5 font-semibold text-white shadow-soft hover:scale-105">
            Find a Therapist
          </Link>
        </div>
      </section>

      <footer className="relative px-4 py-10 text-center text-sm text-ink-soft/70">
        <div className="flex justify-center gap-6 mb-3">
          <Link to="/privacy" className="hover:text-ink">Privacy</Link>
          <Link to="/safety" className="hover:text-ink">Safety hub</Link>
          <Link to="/therapist/apply" className="hover:text-ink">For therapists</Link>
          <Link to="/admin/login" className="hover:text-ink">Admin</Link>
        </div>
        © 2026 SafeVoice
      </footer>

      <ExitSafelyButton />
    </div>
  );
}
