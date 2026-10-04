import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import Blobs from "../components/Blobs";
import api from "../services/api";

export default function Resources() {
  const [items, setItems] = useState([]);
  useEffect(() => { api.listResources().then((d) => setItems(d.resources)); }, []);
  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs variant="quiet" />
      <Navbar />
      <div className="mx-auto max-w-3xl px-6 py-14">
        <h1 className="mb-8 font-display text-3xl font-extrabold">Resources</h1>
        <div className="flex flex-col gap-4">
          {items.map((r) => (
            <div key={r.id} className="glass rounded-3xl p-6 shadow-soft">
              <h3 className="mb-2 font-display font-bold">{r.title}</h3>
              <p className="mb-2 text-sm text-ink-soft">{r.body}</p>
              {r.source_url && <a href={r.source_url} target="_blank" rel="noreferrer" className="text-xs font-semibold text-lavender-deep">Source →</a>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
