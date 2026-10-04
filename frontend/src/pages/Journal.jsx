import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import Blobs from "../components/Blobs";
import ExitSafelyButton from "../components/ExitSafelyButton";
import api from "../services/api";

const MOODS = [["great", "😄"], ["good", "🙂"], ["okay", "😐"], ["low", "😔"], ["struggling", "😞"]];

export default function Journal() {
  const [entries, setEntries] = useState([]);
  const [body, setBody] = useState("");
  const [mood, setMood] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const load = () => api.listJournal().then((d) => setEntries(d.entries)).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);

  const add = async (e) => {
    e.preventDefault();
    if (!body.trim()) return;
    setSaving(true);
    try { await api.createJournalEntry({ body, mood_tag: mood }); setBody(""); setMood(null); await load(); }
    finally { setSaving(false); }
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs variant="quiet" />
      <Navbar />
      <div className="mx-auto max-w-2xl px-6 py-16">
        <h1 className="mb-1 font-display text-3xl font-extrabold">Journal</h1>
        <p className="mb-8 text-sm font-semibold text-lavender-deep">Private — visible only to you.</p>

        <form onSubmit={add} className="glass mb-10 rounded-4xl p-6 shadow-glow">
          <div className="mb-3 flex gap-2">
            {MOODS.map(([m, e]) => (
              <button type="button" key={m} onClick={() => setMood(mood === m ? null : m)} className={`rounded-full px-3 py-1.5 text-sm ${mood === m ? "bg-lavender-deep text-white" : "bg-white/70"}`}>{e} {m}</button>
            ))}
          </div>
          <textarea rows={3} value={body} onChange={(e) => setBody(e.target.value)} placeholder="Write whatever's on your mind…" className="w-full rounded-2xl bg-white/70 px-4 py-3 text-sm outline-none" />
          <button type="submit" disabled={saving} className="mt-3 rounded-full bg-ink px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-60">{saving ? "Saving…" : "Add entry"}</button>
        </form>

        {loading ? <div className="text-ink-soft">Loading…</div> : entries.length === 0 ? <div className="text-ink-soft">No entries yet.</div> : (
          <div className="flex flex-col gap-3">
            {entries.map((e) => (
              <div key={e.id} className="glass rounded-3xl p-5 shadow-soft">
                <div className="mb-2 flex justify-between text-xs text-ink-soft/70">
                  <span>{new Date(e.created_at).toLocaleString()} {e.mood_tag && `· ${e.mood_tag}`}</span>
                  <button onClick={async () => { await api.deleteJournalEntry(e.id); load(); }} className="hover:text-rose-600">Delete</button>
                </div>
                <p className="whitespace-pre-wrap text-sm text-ink">{e.body}</p>
              </div>
            ))}
          </div>
        )}
      </div>
      <ExitSafelyButton />
    </div>
  );
}
