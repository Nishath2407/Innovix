import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import Blobs from "../components/Blobs";
import ExitSafelyButton from "../components/ExitSafelyButton";
import api from "../services/api";

export default function SafetyPlanPage() {
  const [locations, setLocations] = useState([""]);
  const [contacts, setContacts] = useState([{ name: "", phone: "", relationship: "" }]);
  const [reminders, setReminders] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.getSafetyPlan().then((d) => {
      if (d.safety_plan) {
        setLocations(d.safety_plan.safe_locations.length ? d.safety_plan.safe_locations : [""]);
        setContacts(d.safety_plan.trusted_contacts.length ? d.safety_plan.trusted_contacts : [{ name: "", phone: "", relationship: "" }]);
        setReminders(d.safety_plan.personal_reminders || "");
      }
    });
  }, []);

  const save = async () => {
    await api.updateSafetyPlan({ safe_locations: locations.filter((l) => l.trim()), trusted_contacts: contacts.filter((c) => c.name.trim()), personal_reminders: reminders });
    setSaved(true); setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs variant="quiet" />
      <Navbar />
      <div className="mx-auto max-w-2xl px-6 py-14">
        <h1 className="mb-1 font-display text-3xl font-extrabold">My safety plan</h1>
        <p className="mb-8 text-sm font-semibold text-lavender-deep">Private — only you can see this.</p>

        <div className="glass mb-5 rounded-4xl p-7 shadow-soft">
          <h3 className="mb-3 font-display font-bold">Safe locations</h3>
          {locations.map((l, i) => (
            <input key={i} value={l} onChange={(e) => setLocations(locations.map((x, j) => j === i ? e.target.value : x))} placeholder="e.g. Sister's home" className="mb-2 w-full rounded-2xl bg-white/70 px-4 py-2.5 text-sm outline-none" />
          ))}
          <button onClick={() => setLocations([...locations, ""])} className="text-xs font-semibold text-lavender-deep">+ Add another</button>
        </div>

        <div className="glass mb-5 rounded-4xl p-7 shadow-soft">
          <h3 className="mb-3 font-display font-bold">Trusted contacts</h3>
          {contacts.map((c, i) => (
            <div key={i} className="mb-3 grid grid-cols-3 gap-2">
              <input value={c.name} onChange={(e) => setContacts(contacts.map((x, j) => j === i ? { ...x, name: e.target.value } : x))} placeholder="Name" className="rounded-xl bg-white/70 px-3 py-2 text-sm outline-none" />
              <input value={c.phone} onChange={(e) => setContacts(contacts.map((x, j) => j === i ? { ...x, phone: e.target.value } : x))} placeholder="Phone" className="rounded-xl bg-white/70 px-3 py-2 text-sm outline-none" />
              <input value={c.relationship} onChange={(e) => setContacts(contacts.map((x, j) => j === i ? { ...x, relationship: e.target.value } : x))} placeholder="Relationship" className="rounded-xl bg-white/70 px-3 py-2 text-sm outline-none" />
            </div>
          ))}
          <button onClick={() => setContacts([...contacts, { name: "", phone: "", relationship: "" }])} className="text-xs font-semibold text-lavender-deep">+ Add another</button>
        </div>

        <div className="glass mb-6 rounded-4xl p-7 shadow-soft">
          <h3 className="mb-3 font-display font-bold">Personal reminders</h3>
          <textarea value={reminders} onChange={(e) => setReminders(e.target.value)} rows={3} className="w-full rounded-2xl bg-white/70 px-4 py-2.5 text-sm outline-none" />
        </div>

        <button onClick={save} className="rounded-full bg-gradient-to-r from-lavender-deep to-lavender px-6 py-3 text-sm font-semibold text-white">Save plan</button>
        {saved && <span className="ml-3 text-sm text-emerald-600">Saved ✓</span>}
      </div>
      <ExitSafelyButton />
    </div>
  );
}
