import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import Blobs from "../components/Blobs";
import StatusPill from "../components/StatusPill";
import api from "../services/api";

export default function Appointments() {
  const [appts, setAppts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(null);
  const [reviewFor, setReviewFor] = useState(null);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");

  const load = () => api.listAppointments().then((d) => setAppts(d.appointments)).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);

  const cancel = async (id) => {
    setBusy(id);
    try { await api.cancelAppointment(id); await load(); } finally { setBusy(null); }
  };

  const toggleShare = async (a) => {
    setBusy(a.id);
    try { await api.shareSummary(a.id, !a.share_ai_summary); await load(); } finally { setBusy(null); }
  };

  const submitReview = async (id) => {
    await api.reviewAppointment(id, rating, comment);
    setReviewFor(null); setComment(""); setRating(5);
    await load();
  };

  const fmt = (iso) => new Date(iso).toLocaleString([], { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs variant="quiet" />
      <Navbar />
      <div className="mx-auto max-w-3xl px-6 py-14">
        <h1 className="mb-8 font-display text-3xl font-extrabold">Your appointments</h1>
        {loading ? <div className="text-ink-soft">Loading…</div> : appts.length === 0 ? (
          <div className="glass rounded-4xl p-8 text-center text-ink-soft shadow-soft">
            No appointments yet. <Link to="/therapists" className="font-semibold text-lavender-deep">Find a therapist →</Link>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {appts.map((a) => (
              <div key={a.id} className="glass rounded-4xl p-6 shadow-soft">
                <div className="mb-2 flex items-start justify-between">
                  <div>
                    <div className="font-display font-bold">{a.therapist_name}</div>
                    <div className="text-sm text-ink-soft">{fmt(a.scheduled_start)} · {a.session_mode}</div>
                  </div>
                  <StatusPill status={a.status} />
                </div>

                {a.status === "pending" && (
                  <Link to="/therapists" className="text-sm font-medium text-amber-600">Payment pending — hold expires soon</Link>
                )}

                {["requested", "confirmed"].includes(a.status) && (
                  <label className="mt-2 flex items-center gap-2 text-sm text-ink-soft">
                    <input type="checkbox" checked={a.share_ai_summary} onChange={() => toggleShare(a)} disabled={busy === a.id} />
                    Share my private check-in summary with this therapist
                  </label>
                )}

                <div className="mt-4 flex flex-wrap gap-2">
                  {a.status === "confirmed" && a.can_join && (
                    <Link to={`/session/${a.session_id || ""}?appt=${a.id}`} className="rounded-full bg-gradient-to-r from-lavender-deep to-lavender px-4 py-2 text-xs font-semibold text-white">
                      Join session
                    </Link>
                  )}
                  {a.status === "confirmed" && !a.can_join && <span className="text-xs text-ink-soft/70">{a.join_hint}</span>}
                  {["pending", "requested", "confirmed"].includes(a.status) && (
                    <button disabled={busy === a.id} onClick={() => cancel(a.id)} className="rounded-full bg-white/70 px-4 py-2 text-xs font-semibold text-rose-600">
                      {a.status === "pending" ? "Release hold" : "Cancel"}
                    </button>
                  )}
                  {a.status === "completed" && !a.reviewed && (
                    <button onClick={() => setReviewFor(a.id)} className="rounded-full bg-white/70 px-4 py-2 text-xs font-semibold text-ink-soft">Leave a review</button>
                  )}
                </div>

                {reviewFor === a.id && (
                  <div className="mt-4 rounded-2xl bg-white/60 p-4">
                    <div className="mb-2 flex gap-1">
                      {[1, 2, 3, 4, 5].map((n) => (
                        <button key={n} onClick={() => setRating(n)} className={n <= rating ? "text-amber-500" : "text-ink-soft/30"}>★</button>
                      ))}
                    </div>
                    <textarea value={comment} onChange={(e) => setComment(e.target.value)} placeholder="How did it go?" className="mb-2 w-full rounded-xl bg-white/80 p-2 text-sm outline-none" rows={2} />
                    <button onClick={() => submitReview(a.id)} className="rounded-full bg-ink px-4 py-2 text-xs font-semibold text-white">Submit</button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
