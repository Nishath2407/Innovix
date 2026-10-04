import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import Navbar from "../components/Navbar";
import StatusPill from "../components/StatusPill";
import api from "../services/api";

const TABS = ["Overview", "Users", "Therapists", "Payments", "Resources", "Audit log"];
const COLORS = ["#7C5CFC", "#5EEAD4", "#FFB4A2"];

export default function AdminDashboard() {
  const [tab, setTab] = useState("Overview");
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="mx-auto max-w-6xl px-6 py-10">
        <h1 className="mb-6 font-display text-3xl font-extrabold">Admin — Platform monitoring</h1>
        <div className="mb-6 flex gap-2 overflow-x-auto">
          {TABS.map((t) => (
            <button key={t} onClick={() => setTab(t)} className={`shrink-0 rounded-full px-4 py-2 text-sm font-semibold ${tab === t ? "bg-ink text-white" : "bg-white text-ink-soft shadow-sm"}`}>{t}</button>
          ))}
        </div>
        {tab === "Overview" && <Overview />}
        {tab === "Users" && <Users />}
        {tab === "Therapists" && <Therapists />}
        {tab === "Payments" && <Payments />}
        {tab === "Resources" && <Resources />}
        {tab === "Audit log" && <AuditLog />}
      </div>
    </div>
  );
}

const Card = ({ children, className = "" }) => <div className={`rounded-3xl bg-white p-6 shadow-sm ${className}`}>{children}</div>;

function Overview() {
  const [a, setA] = useState(null);
  const [sys, setSys] = useState(null);
  useEffect(() => { api.adminAnalytics().then(setA); api.adminSystem().then(setSys); }, []);
  if (!a) return <div className="text-ink-soft">Loading…</div>;

  const stat = (label, value, warn) => (
    <Card className="text-center">
      <div className={`font-display text-2xl font-extrabold ${warn ? "text-rose-600" : "text-ink"}`}>{value}</div>
      <div className="text-xs text-ink-soft">{label}</div>
    </Card>
  );

  return (
    <div className="flex flex-col gap-6">
      {sys && (
        <div className="flex flex-wrap gap-2 text-xs">
          {Object.entries({ API: sys.api, Database: sys.database, Email: sys.email, Payments: sys.payments, Environment: sys.environment }).map(([k, v]) => (
            <span key={k} className={`rounded-full px-3 py-1 font-semibold ${v === "ok" ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-600"}`}>{k}: {v}</span>
          ))}
        </div>
      )}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {stat("Users", a.totals.users)}
        {stat("Active (7d)", a.totals.active_users)}
        {stat("Therapists", a.totals.therapists)}
        {stat("Pending review", a.totals.pending_verification, a.totals.pending_verification > 0)}
        {stat("Appointments", a.totals.appointments)}
        {stat("Completed sessions", a.totals.completed_sessions)}
        {stat("Live now", a.totals.live_sessions)}
        {stat("Revenue (₹)", a.totals.revenue)}
        {stat("Refunds pending", a.totals.refunds_pending, a.totals.refunds_pending > 0)}
        {stat("High-concern check-ins (7d)", a.totals.high_concern_checkins_7d, a.totals.high_concern_checkins_7d > 0)}
        {stat("Flagged reviews", a.totals.flagged_reviews, a.totals.flagged_reviews > 0)}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <h3 className="mb-3 font-display font-bold">Signups (14 days)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={a.series.signups}><XAxis dataKey="date" tick={{ fontSize: 9 }} /><YAxis allowDecimals={false} tick={{ fontSize: 10 }} /><Tooltip /><Line type="monotone" dataKey="value" stroke="#7C5CFC" strokeWidth={2} dot={false} /></LineChart>
          </ResponsiveContainer>
        </Card>
        <Card>
          <h3 className="mb-3 font-display font-bold">Appointments booked (14 days)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={a.series.appointments}><XAxis dataKey="date" tick={{ fontSize: 9 }} /><YAxis allowDecimals={false} tick={{ fontSize: 10 }} /><Tooltip /><Line type="monotone" dataKey="value" stroke="#5EEAD4" strokeWidth={2} dot={false} /></LineChart>
          </ResponsiveContainer>
        </Card>
        <Card>
          <h3 className="mb-3 font-display font-bold">Session types</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={a.session_types} dataKey="count" nameKey="mode" outerRadius={70} label>
                {a.session_types.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>
        <Card>
          <h3 className="mb-3 font-display font-bold">Top therapists (completed sessions)</h3>
          <div className="flex flex-col gap-2">
            {a.top_therapists.map((t) => (
              <div key={t.name} className="flex justify-between text-sm"><span>{t.name}</span><span className="font-semibold">{t.sessions}</span></div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

function Users() {
  const [items, setItems] = useState([]);
  const [role, setRole] = useState("user");
  const load = () => api.adminUsers({ role }).then((d) => setItems(d.items));
  useEffect(() => { load(); }, [role]);

  const act = async (u) => { u.is_active ? await api.suspendUser(u.id) : await api.activateUser(u.id); load(); };

  return (
    <Card>
      <div className="mb-4 flex gap-2">
        {["user", "therapist"].map((r) => <button key={r} onClick={() => setRole(r)} className={`rounded-full px-3 py-1.5 text-xs font-semibold capitalize ${role === r ? "bg-ink text-white" : "bg-gray-100"}`}>{r}s</button>)}
      </div>
      <table className="w-full text-sm">
        <thead><tr className="text-left text-xs text-ink-soft"><th className="pb-2">Name</th><th>Email</th><th>Status</th><th>Joined</th><th></th></tr></thead>
        <tbody>
          {items.map((u) => (
            <tr key={u.id} className="border-t border-gray-100">
              <td className="py-2">{u.display_name}</td>
              <td className="text-ink-soft">{u.email}</td>
              <td>{u.is_active ? <span className="text-emerald-600">Active</span> : <span className="text-rose-600">Suspended</span>}</td>
              <td className="text-ink-soft">{new Date(u.created_at).toLocaleDateString()}</td>
              <td><button onClick={() => act(u)} className={`rounded-full px-3 py-1 text-xs font-semibold ${u.is_active ? "bg-rose-100 text-rose-600" : "bg-emerald-100 text-emerald-600"}`}>{u.is_active ? "Suspend" : "Reactivate"}</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

function Therapists() {
  const [items, setItems] = useState([]);
  const [status, setStatus] = useState("pending");
  const load = () => api.adminTherapists({ status }).then((d) => setItems(d.items));
  useEffect(() => { load(); }, [status]);

  const verify = async (id, approve) => { await api.verifyTherapist(id, approve); load(); };

  return (
    <Card>
      <div className="mb-4 flex gap-2">
        {["pending", "approved", "rejected"].map((s) => <button key={s} onClick={() => setStatus(s)} className={`rounded-full px-3 py-1.5 text-xs font-semibold capitalize ${status === s ? "bg-ink text-white" : "bg-gray-100"}`}>{s}</button>)}
      </div>
      <div className="flex flex-col gap-3">
        {items.length === 0 && <p className="text-sm text-ink-soft">Nothing here.</p>}
        {items.map((t) => (
          <div key={t.id} className="rounded-2xl border border-gray-100 p-4">
            <div className="mb-2 flex items-start justify-between">
              <div><div className="font-semibold">{t.display_name}</div><div className="text-xs text-ink-soft">{t.qualification} · {t.years_experience} yrs · {t.email}</div></div>
              <StatusPill status={t.verification_status} />
            </div>
            <div className="mb-2 flex flex-wrap gap-1">{t.specializations.map((s) => <span key={s} className="rounded-full bg-gray-100 px-2 py-0.5 text-xs">{s}</span>)}</div>
            {t.credentials.map((c, i) => <div key={i} className="text-xs text-ink-soft">{c.type}: {c.details}</div>)}
            {status === "pending" && (
              <div className="mt-3 flex gap-2">
                <button onClick={() => verify(t.id, true)} className="rounded-full bg-emerald-500 px-4 py-1.5 text-xs font-semibold text-white">Approve</button>
                <button onClick={() => verify(t.id, false)} className="rounded-full bg-rose-100 px-4 py-1.5 text-xs font-semibold text-rose-600">Reject</button>
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}

function Payments() {
  const [items, setItems] = useState([]);
  const load = () => api.adminPayments({}).then((d) => setItems(d.items));
  useEffect(() => { load(); }, []);
  return (
    <Card>
      <table className="w-full text-sm">
        <thead><tr className="text-left text-xs text-ink-soft"><th className="pb-2">Amount</th><th>Status</th><th>Mode</th><th>Date</th><th></th></tr></thead>
        <tbody>
          {items.map((p) => (
            <tr key={p.id} className="border-t border-gray-100">
              <td className="py-2">₹{p.amount_rupees}</td>
              <td><StatusPill status={p.status} /></td>
              <td className="text-ink-soft">{p.mode}</td>
              <td className="text-ink-soft">{new Date(p.created_at).toLocaleDateString()}</td>
              <td>{p.status === "refund_pending" && <button onClick={async () => { await api.markRefunded(p.id); load(); }} className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">Mark refunded</button>}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

function Resources() {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({ title: "", body: "", category: "anxiety", source_url: "" });
  const load = () => api.adminResources().then((d) => setItems(d.items));
  useEffect(() => { load(); }, []);
  const create = async () => { await api.createResource(form); setForm({ title: "", body: "", category: "anxiety", source_url: "" }); load(); };
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <h3 className="mb-3 font-display font-bold">Add resource</h3>
        <div className="flex flex-col gap-2">
          <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Title" className="rounded-xl bg-gray-50 px-3 py-2 text-sm" />
          <textarea value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} placeholder="Body" rows={3} className="rounded-xl bg-gray-50 px-3 py-2 text-sm" />
          <input value={form.source_url} onChange={(e) => setForm({ ...form, source_url: e.target.value })} placeholder="Source URL (optional)" className="rounded-xl bg-gray-50 px-3 py-2 text-sm" />
          <button onClick={create} className="self-start rounded-full bg-ink px-5 py-2 text-sm font-semibold text-white">Publish</button>
        </div>
      </Card>
      <Card>
        <h3 className="mb-3 font-display font-bold">Published resources</h3>
        <div className="flex flex-col gap-2">
          {items.map((r) => (
            <div key={r.id} className="flex items-center justify-between rounded-xl bg-gray-50 px-3 py-2 text-sm">
              <span>{r.title}</span>
              <button onClick={async () => { await api.deleteResource(r.id); load(); }} className="text-xs text-rose-600">Delete</button>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function AuditLog() {
  const [items, setItems] = useState([]);
  useEffect(() => { api.auditLogs({}).then((d) => setItems(d.items)); }, []);
  return (
    <Card>
      <div className="flex flex-col gap-2">
        {items.map((l) => (
          <div key={l.id} className="flex justify-between border-b border-gray-100 py-2 text-sm">
            <span><b>{l.actor}</b> — {l.action.replace(/_/g, " ")}</span>
            <span className="text-xs text-ink-soft">{new Date(l.created_at).toLocaleString()}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}
