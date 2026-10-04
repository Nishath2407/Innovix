import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import Blobs from "../components/Blobs";
import StatusPill from "../components/StatusPill";
import api from "../services/api";
import { CONCERNS, LANGUAGES, SESSION_MODES } from "../constants";

const TABS = ["Overview", "Requests", "Availability", "Profile", "Earnings"];
const DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function TherapistDashboard() {
  const [tab, setTab] = useState("Overview");
  const [overview, setOverview] = useState(null);

  const load = () => api.therapistOverview().then(setOverview);
  useEffect(() => { load(); }, []);

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs variant="quiet" />
      <Navbar />
      <div className="mx-auto max-w-5xl px-6 py-10">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <h1 className="font-display text-3xl font-extrabold">Therapist dashboard</h1>
          {overview && (
            <div className="flex gap-3 text-sm">
              <Badge label="Requests" value={overview.counts.requests} color="bg-sky-100 text-sky-700" />
              <Badge label="Upcoming" value={overview.counts.upcoming} color="bg-emerald-100 text-emerald-700" />
              <Badge label="Completed" value={overview.counts.completed} color="bg-violet-100 text-violet-700" />
              {overview.rating.count > 0 && <Badge label="Rating" value={`★ ${overview.rating.avg}`} color="bg-amber-100 text-amber-700" />}
            </div>
          )}
        </div>

        {overview && !overview.profile.is_verified && (
          <div className="glass mb-6 rounded-3xl border border-amber-200 p-5 text-sm text-amber-700 shadow-soft">
            Your profile is pending admin review. Clients can't find you yet — this usually doesn't take long.
          </div>
        )}

        <div className="mb-6 flex gap-2 overflow-x-auto">
          {TABS.map((t) => (
            <button key={t} onClick={() => setTab(t)} className={`shrink-0 rounded-full px-4 py-2 text-sm font-semibold ${tab === t ? "bg-ink text-white" : "bg-white/70 text-ink-soft"}`}>{t}</button>
          ))}
        </div>

        {tab === "Overview" && overview && <Overview data={overview} />}
        {tab === "Requests" && <Requests onChange={load} />}
        {tab === "Availability" && <Availability />}
        {tab === "Profile" && overview && <ProfileTab profile={overview.profile} onSaved={load} />}
        {tab === "Earnings" && <Earnings />}
      </div>
    </div>
  );
}

function Badge({ label, value, color }) {
  return <div className={`rounded-full px-3 py-1.5 font-semibold ${color}`}>{value} {label}</div>;
}

function Overview({ data }) {
  const fmt = (iso) => new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return (
    <div className="glass rounded-4xl p-7 shadow-soft">
      <h3 className="mb-4 font-display font-bold">Today</h3>
      {data.today.length === 0 ? <p className="text-ink-soft">No sessions scheduled today.</p> : (
        <div className="flex flex-col gap-3">
          {data.today.map((a) => (
            <div key={a.id} className="flex items-center justify-between rounded-2xl bg-white/60 p-4">
              <div><div className="font-semibold">{a.client_name}</div><div className="text-xs text-ink-soft">{fmt(a.scheduled_start)} · {a.mode}</div></div>
              <StatusPill status={a.status} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Requests({ onChange }) {
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState("requested");
  const [busy, setBusy] = useState(null);
  const [summaries, setSummaries] = useState({});

  const load = () => api.therapistAppointments(filter === "all" ? undefined : filter).then((d) => setItems(d.appointments));
  useEffect(() => { load(); }, [filter]);

  const respond = async (id, action) => {
    setBusy(id);
    try { await api.respondToAppointment(id, action); await load(); onChange?.(); } finally { setBusy(null); }
  };

  const viewSummary = async (id) => {
    const s = await api.preSessionSummary(id);
    setSummaries((prev) => ({ ...prev, [id]: s }));
  };

  const fmt = (iso) => new Date(iso).toLocaleString([], { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

  return (
    <div>
      <div className="mb-4 flex gap-2">
        {["requested", "confirmed", "completed", "all"].map((f) => (
          <button key={f} onClick={() => setFilter(f)} className={`rounded-full px-3 py-1.5 text-xs font-semibold capitalize ${filter === f ? "bg-lavender-deep text-white" : "bg-white/70 text-ink-soft"}`}>{f}</button>
        ))}
      </div>
      {items.length === 0 ? <p className="text-ink-soft">Nothing here.</p> : (
        <div className="flex flex-col gap-3">
          {items.map((a) => (
            <div key={a.id} className="glass rounded-3xl p-5 shadow-soft">
              <div className="mb-2 flex items-start justify-between">
                <div><div className="font-semibold">{a.client_name}</div><div className="text-xs text-ink-soft">{fmt(a.scheduled_start)} · {a.mode}</div></div>
                <StatusPill status={a.status} />
              </div>
              {a.status === "requested" && (
                <div className="flex gap-2">
                  <button disabled={busy === a.id} onClick={() => respond(a.id, "accept")} className="rounded-full bg-emerald-500 px-4 py-2 text-xs font-semibold text-white">Accept</button>
                  <button disabled={busy === a.id} onClick={() => respond(a.id, "decline")} className="rounded-full bg-rose-100 px-4 py-2 text-xs font-semibold text-rose-600">Decline</button>
                  <button onClick={() => viewSummary(a.id)} className="rounded-full bg-white/70 px-4 py-2 text-xs font-semibold text-ink-soft">Pre-session notes</button>
                </div>
              )}
              {a.status === "confirmed" && a.can_join && (
                <Link to={`/session/${a.session_id || ""}?appt=${a.id}`} className="inline-block rounded-full bg-gradient-to-r from-lavender-deep to-lavender px-4 py-2 text-xs font-semibold text-white">Join session</Link>
              )}
              {a.status === "confirmed" && !a.can_join && <span className="text-xs text-ink-soft/70">{a.join_hint}</span>}
              {summaries[a.id] && (
                <div className="mt-3 rounded-2xl bg-white/60 p-3 text-xs">
                  {summaries[a.id].shared ? (
                    summaries[a.id].summary ? (
                      <>Primary emotion: <b>{summaries[a.id].summary.primary_emotion}</b> · Concern level: <b>{summaries[a.id].summary.concern_level || "n/a"}</b><br /><span className="text-ink-soft">{summaries[a.id].summary.note}</span></>
                    ) : <span className="text-ink-soft">No check-in completed yet.</span>
                  ) : <span className="text-ink-soft">{summaries[a.id].message}</span>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Availability() {
  const [rows, setRows] = useState([]);
  const [saved, setSaved] = useState(false);

  useEffect(() => { api.getAvailability().then((d) => setRows(d.availability)); }, []);

  const addRow = () => setRows([...rows, { weekday: 0, start: "09:00", end: "17:00" }]);
  const updateRow = (i, field, val) => setRows(rows.map((r, j) => j === i ? { ...r, [field]: field === "weekday" ? Number(val) : val } : r));
  const removeRow = (i) => setRows(rows.filter((_, j) => j !== i));

  const save = async () => { await api.setAvailability(rows); setSaved(true); setTimeout(() => setSaved(false), 2000); };

  return (
    <div className="glass rounded-4xl p-7 shadow-soft">
      <h3 className="mb-4 font-display font-bold">Weekly availability (IST)</h3>
      <div className="mb-4 flex flex-col gap-2">
        {rows.map((r, i) => (
          <div key={i} className="flex items-center gap-2">
            <select value={r.weekday} onChange={(e) => updateRow(i, "weekday", e.target.value)} className="rounded-xl bg-white/70 px-3 py-2 text-sm">
              {DAY_NAMES.map((d, idx) => <option key={idx} value={idx}>{d}</option>)}
            </select>
            <input type="time" value={r.start} onChange={(e) => updateRow(i, "start", e.target.value)} className="rounded-xl bg-white/70 px-3 py-2 text-sm" />
            <span className="text-ink-soft">to</span>
            <input type="time" value={r.end} onChange={(e) => updateRow(i, "end", e.target.value)} className="rounded-xl bg-white/70 px-3 py-2 text-sm" />
            <button onClick={() => removeRow(i)} className="text-rose-500">✕</button>
          </div>
        ))}
      </div>
      <div className="flex gap-3">
        <button onClick={addRow} className="rounded-full bg-white/70 px-4 py-2 text-sm font-semibold text-ink-soft">+ Add window</button>
        <button onClick={save} className="rounded-full bg-gradient-to-r from-lavender-deep to-lavender px-5 py-2 text-sm font-semibold text-white">Save</button>
        {saved && <span className="self-center text-sm text-emerald-600">Saved ✓</span>}
      </div>
    </div>
  );
}

function ProfileTab({ profile, onSaved }) {
  const [form, setForm] = useState({ ...profile });
  const [saving, setSaving] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const toggle = (k, v) => setForm((f) => ({ ...f, [k]: f[k].includes(v) ? f[k].filter((x) => x !== v) : [...f[k], v] }));

  const save = async () => {
    setSaving(true);
    try {
      await api.updateTherapistProfile({
        display_name: form.display_name, qualification: form.qualification, bio: form.bio, approach: form.approach,
        session_price: Number(form.session_price), years_experience: Number(form.years_experience),
        is_accepting_clients: form.is_accepting_clients, session_modes: form.session_modes,
        specializations: form.specializations, languages: form.languages,
      });
      onSaved?.();
    } finally { setSaving(false); }
  };

  return (
    <div className="glass flex flex-col gap-4 rounded-4xl p-7 shadow-soft">
      {!profile.is_verified && <div className="rounded-2xl bg-amber-50 p-3 text-xs text-amber-700">Pending review — {profile.verification_status}</div>}
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_accepting_clients} onChange={(e) => set("is_accepting_clients", e.target.checked)} /> Currently accepting new clients</label>
      <input value={form.display_name} onChange={(e) => set("display_name", e.target.value)} placeholder="Display name" className="input" />
      <input value={form.qualification} onChange={(e) => set("qualification", e.target.value)} placeholder="Qualification" className="input" />
      <div className="grid grid-cols-2 gap-3">
        <input type="number" value={form.session_price} onChange={(e) => set("session_price", e.target.value)} placeholder="Session price (₹)" className="input" />
        <input type="number" value={form.years_experience} onChange={(e) => set("years_experience", e.target.value)} placeholder="Years experience" className="input" />
      </div>
      <textarea rows={3} value={form.bio} onChange={(e) => set("bio", e.target.value)} placeholder="Bio" className="input" />
      <textarea rows={2} value={form.approach} onChange={(e) => set("approach", e.target.value)} placeholder="Approach" className="input" />
      <ChipGroup label="Specializations" options={CONCERNS} value={form.specializations} onToggle={(v) => toggle("specializations", v)} />
      <ChipGroup label="Languages" options={LANGUAGES} value={form.languages} onToggle={(v) => toggle("languages", v)} />
      <ChipGroup label="Session types" options={SESSION_MODES} value={form.session_modes} onToggle={(v) => toggle("session_modes", v)} />
      <button onClick={save} disabled={saving} className="self-start rounded-full bg-gradient-to-r from-lavender-deep to-lavender px-6 py-2.5 text-sm font-semibold text-white disabled:opacity-60">
        {saving ? "Saving…" : "Save profile"}
      </button>
      <style>{`.input { border-radius: 1rem; background: rgba(255,255,255,0.7); padding: 0.65rem 1rem; font-size: 0.875rem; outline: none; }`}</style>
    </div>
  );
}

function ChipGroup({ label, options, value, onToggle }) {
  return (
    <div>
      <div className="mb-2 text-xs font-semibold text-ink-soft">{label}</div>
      <div className="flex flex-wrap gap-2">
        {options.map((o) => (
          <button type="button" key={o.value} onClick={() => onToggle(o.value)} className={`rounded-full px-3 py-1.5 text-xs font-medium ${value.includes(o.value) ? "bg-lavender-deep text-white" : "bg-white/70 text-ink-soft"}`}>{o.label}</button>
        ))}
      </div>
    </div>
  );
}

function Earnings() {
  const [data, setData] = useState(null);
  useEffect(() => { api.therapistEarnings().then(setData); }, []);
  if (!data) return null;
  return (
    <div className="glass rounded-4xl p-7 shadow-soft">
      <div className="mb-6 grid grid-cols-3 gap-4">
        <div className="text-center"><div className="font-display text-2xl font-extrabold text-lavender-deep">₹{data.total_earned}</div><div className="text-xs text-ink-soft">Total earned</div></div>
        <div className="text-center"><div className="font-display text-2xl font-extrabold">{data.completed_sessions}</div><div className="text-xs text-ink-soft">Completed</div></div>
        <div className="text-center"><div className="font-display text-2xl font-extrabold">₹{data.upcoming_value}</div><div className="text-xs text-ink-soft">Upcoming value</div></div>
      </div>
      <p className="text-xs text-ink-soft/70">{data.note}</p>
    </div>
  );
}
