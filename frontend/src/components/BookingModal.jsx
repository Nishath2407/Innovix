import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

const MODE_LABEL = { video: "Video", audio: "Audio", text: "Text" };

export default function BookingModal({ therapist, onClose }) {
  const navigate = useNavigate();
  const [days, setDays] = useState([]);
  const [selectedDay, setSelectedDay] = useState(0);
  const [slot, setSlot] = useState(null);
  const [mode, setMode] = useState(therapist.session_modes[0] || "video");
  const [step, setStep] = useState("pick"); // pick -> pay -> done
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [appointment, setAppointment] = useState(null);

  useEffect(() => {
    api.getSlots(therapist.id, 7).then((d) => setDays(d.days)).catch(() => setError("Couldn't load availability.")).finally(() => setLoading(false));
  }, [therapist.id]);

  const book = async () => {
    setError("");
    try {
      const { appointment } = await api.createAppointment({ therapist_id: therapist.id, scheduled_start: slot, session_mode: mode });
      setAppointment(appointment);
      setStep("pay");
    } catch (err) {
      setError(err.payload?.message || "Couldn't book that slot. Please try another.");
    }
  };

  const pay = async () => {
    setError("");
    try {
      const order = await api.createPaymentOrder(appointment.id);
      if (order.mode === "test") {
        await api.confirmTestPayment(order.payment_id);
      } else {
        setError("Live payments aren't configured on this server yet. Set RAZORPAY_KEY_ID/SECRET to enable real payments.");
        return;
      }
      setStep("done");
    } catch (err) {
      setError(err.payload?.message || "Payment couldn't be completed.");
    }
  };

  const fmt = (iso) => new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const fmtDay = (iso) => new Date(iso).toLocaleDateString([], { weekday: "short", day: "numeric" });

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-ink/40 backdrop-blur-sm sm:items-center" onClick={onClose}>
      <div className="glass max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-t-4xl p-7 shadow-glow sm:rounded-4xl" onClick={(e) => e.stopPropagation()}>
        <div className="mb-5 flex items-center justify-between">
          <h3 className="font-display text-xl font-bold">Book with {therapist.display_name}</h3>
          <button onClick={onClose} className="text-ink-soft hover:text-ink">✕</button>
        </div>

        {step === "pick" && (
          <>
            <div className="mb-4 flex gap-2">
              {therapist.session_modes.map((m) => (
                <button key={m} onClick={() => setMode(m)} className={`rounded-full px-4 py-2 text-sm font-medium ${mode === m ? "bg-lavender-deep text-white" : "bg-white/70 text-ink-soft"}`}>
                  {MODE_LABEL[m]}
                </button>
              ))}
            </div>

            {loading ? <div className="text-ink-soft">Loading availability…</div> : (
              <>
                <div className="mb-3 flex gap-2 overflow-x-auto pb-1">
                  {days.map((d, i) => (
                    <button key={d.date} onClick={() => { setSelectedDay(i); setSlot(null); }}
                      disabled={d.slots.length === 0}
                      className={`shrink-0 rounded-2xl px-3 py-2 text-xs font-medium disabled:opacity-30 ${selectedDay === i ? "bg-ink text-white" : "bg-white/70 text-ink-soft"}`}>
                      {new Date(d.date).toLocaleDateString([], { weekday: "short", day: "numeric" })}
                    </button>
                  ))}
                </div>
                <div className="mb-5 grid grid-cols-3 gap-2">
                  {(days[selectedDay]?.slots || []).length === 0 && <div className="col-span-3 text-sm text-ink-soft">No openings this day.</div>}
                  {(days[selectedDay]?.slots || []).map((s) => (
                    <button key={s} onClick={() => setSlot(s)} className={`rounded-xl py-2 text-sm font-medium ${slot === s ? "bg-lavender-deep text-white" : "bg-white/70 text-ink-soft hover:bg-white"}`}>
                      {fmt(s)}
                    </button>
                  ))}
                </div>
              </>
            )}
            {error && <div className="mb-3 text-sm text-rose-600">{error}</div>}
            <button disabled={!slot} onClick={book} className="w-full rounded-2xl bg-gradient-to-r from-lavender-deep to-lavender py-3 text-sm font-semibold text-white disabled:opacity-40">
              Continue — ₹{therapist.session_price}
            </button>
          </>
        )}

        {step === "pay" && (
          <>
            <div className="mb-5 rounded-2xl bg-white/60 p-4 text-sm">
              <div className="flex justify-between py-1"><span className="text-ink-soft">Session</span><span>{MODE_LABEL[mode]}</span></div>
              <div className="flex justify-between py-1"><span className="text-ink-soft">Time</span><span>{fmtDay(slot)}, {fmt(slot)}</span></div>
              <div className="flex justify-between py-1 font-semibold"><span>Total</span><span>₹{therapist.session_price}</span></div>
            </div>
            <p className="mb-3 text-xs text-ink-soft/80">Your slot is held for 15 minutes. Complete payment to send your request — the therapist confirms before the session is booked.</p>
            {error && <div className="mb-3 text-sm text-rose-600">{error}</div>}
            <button onClick={pay} className="w-full rounded-2xl bg-ink py-3 text-sm font-semibold text-white">Pay & send request</button>
          </>
        )}

        {step === "done" && (
          <div className="text-center">
            <div className="mb-3 text-4xl">✅</div>
            <h4 className="mb-2 font-display text-lg font-bold">Request sent</h4>
            <p className="mb-6 text-sm text-ink-soft">{therapist.display_name} will confirm shortly. You'll see it in your appointments.</p>
            <button onClick={() => navigate("/appointments")} className="w-full rounded-2xl bg-gradient-to-r from-lavender-deep to-lavender py-3 text-sm font-semibold text-white">
              View my appointments
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
