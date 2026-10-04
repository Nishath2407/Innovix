import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import Blobs from "../components/Blobs";
import api from "../services/api";
import { CONCERNS, LANGUAGES } from "../constants";
import BookingModal from "../components/BookingModal";

export default function Therapists() {
  const [therapists, setTherapists] = useState([]);
  const [emptyMessage, setEmptyMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({});
  const [booking, setBooking] = useState(null);

  const fetchTherapists = async (params) => {
    setLoading(true); setError("");
    try {
      const data = await api.listTherapists(params);
      setTherapists(data.therapists);
      setEmptyMessage(data.empty_message || "");
    } catch {
      setError("Couldn't load therapists right now. Please try again shortly.");
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchTherapists({}); }, []);

  const applyFilter = (key, value) => {
    const next = { ...filters, [key]: value };
    if (!value) delete next[key];
    setFilters(next);
    fetchTherapists(next);
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs variant="quiet" />
      <Navbar />
      <div className="mx-auto max-w-6xl px-6 py-14">
        <h1 className="mb-2 font-display text-3xl font-extrabold">Find your therapist</h1>
        <p className="mb-8 max-w-2xl text-ink-soft">Every profile shows specializations, languages, and pricing up front.</p>

        <div className="mb-8 flex flex-wrap gap-2">
          <select onChange={(e) => applyFilter("specialization", e.target.value)} className="filter-select">
            <option value="">All specializations</option>
            {CONCERNS.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
          <select onChange={(e) => applyFilter("language", e.target.value)} className="filter-select">
            <option value="">All languages</option>
            {LANGUAGES.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
          </select>
          <select onChange={(e) => applyFilter("max_price", e.target.value)} className="filter-select">
            <option value="">Any budget</option>
            <option value="1000">Under ₹1,000</option><option value="1500">Under ₹1,500</option><option value="2000">Under ₹2,000</option>
          </select>
          <select onChange={(e) => applyFilter("mode", e.target.value)} className="filter-select">
            <option value="">Any session type</option>
            <option value="video">Video</option><option value="audio">Audio</option><option value="text">Text</option>
          </select>
        </div>

        {loading && <div className="text-ink-soft">Loading therapists…</div>}
        {error && <div className="text-rose-600">{error}</div>}
        {!loading && !error && therapists.length === 0 && <div className="text-ink-soft">{emptyMessage || "No therapists found."}</div>}

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {therapists.map((t) => (
            <div key={t.id} className="glass flex flex-col rounded-4xl p-6 shadow-soft transition hover:-translate-y-1">
              <div className="mb-3 flex items-center gap-3">
                <div className="grid h-11 w-11 place-items-center rounded-full bg-gradient-to-br from-lavender to-mint font-display font-bold text-white">{t.display_name[0]}</div>
                <div>
                  <div className="font-semibold">{t.display_name}</div>
                  <div className="text-xs text-ink-soft/80">{t.qualification} · {t.years_experience} yrs</div>
                </div>
              </div>
              <div className="mb-4 flex flex-wrap gap-1.5">
                {t.specializations.slice(0, 3).map((s) => (
                  <span key={s} className="rounded-full bg-white/70 px-2.5 py-1 text-xs text-ink-soft">{CONCERNS.find((c) => c.value === s)?.label || s}</span>
                ))}
              </div>
              {t.rating_count > 0 && <div className="mb-3 text-xs text-amber-600">★ {t.rating_avg} ({t.rating_count})</div>}
              <div className="mt-auto flex items-center justify-between border-t border-line pt-3 text-sm">
                <span className="font-semibold">₹{t.session_price}</span>
                <span className="flex items-center gap-1 text-xs text-emerald-600">✓ Verified</span>
              </div>
              <button onClick={() => setBooking(t)} className="mt-3 rounded-full bg-ink py-2.5 text-sm font-semibold text-white hover:bg-ink/90">
                Book a session
              </button>
            </div>
          ))}
        </div>
      </div>
      {booking && <BookingModal therapist={booking} onClose={() => setBooking(null)} />}
      <style>{`.filter-select { border-radius: 999px; background: rgba(255,255,255,0.7); padding: 0.55rem 1rem; font-size: 0.85rem; border: none; outline: none; }`}</style>
    </div>
  );
}
