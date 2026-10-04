import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";
import Navbar from "../components/Navbar";
import Blobs from "../components/Blobs";
import api from "../services/api";

export default function Progress() {
  const [data, setData] = useState(null);
  useEffect(() => { api.getProgress().then(setData); }, []);

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blobs variant="quiet" />
      <Navbar />
      <div className="mx-auto max-w-3xl px-6 py-14">
        <h1 className="mb-1 font-display text-3xl font-extrabold">Your progress</h1>
        <p className="mb-8 text-ink-soft">Reflects what you've logged — not a medical assessment.</p>
        {!data ? <div className="text-ink-soft">Loading…</div> : (
          <div className="flex flex-col gap-6">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              {Object.entries({ "Check-ins": data.totals.checkins, "Journal entries": data.totals.journal_entries, "Sessions done": data.totals.sessions_completed, "Recovery streak": data.totals.recovery_streak }).map(([k, v]) => (
                <div key={k} className="glass rounded-3xl p-4 text-center shadow-soft">
                  <div className="font-display text-2xl font-extrabold text-lavender-deep">{v}</div>
                  <div className="text-xs text-ink-soft">{k}</div>
                </div>
              ))}
            </div>
            {data.mood_trend.length > 0 && (
              <div className="glass rounded-4xl p-6 shadow-soft">
                <h3 className="mb-4 font-display font-bold">Mood over time</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={data.mood_trend}>
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis domain={[0, 5]} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="score" stroke="#7C5CFC" strokeWidth={3} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
            {data.emotion_counts.length > 0 && (
              <div className="glass rounded-4xl p-6 shadow-soft">
                <h3 className="mb-4 font-display font-bold">Emotions noticed in check-ins</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={data.emotion_counts}>
                    <XAxis dataKey="emotion" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#5EEAD4" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
            <p className="text-xs text-ink-soft/70">{data.note}</p>
          </div>
        )}
      </div>
    </div>
  );
}
