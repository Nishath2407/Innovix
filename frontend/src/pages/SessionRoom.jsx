import { useEffect, useRef, useState } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import { io } from "socket.io-client";
import Navbar from "../components/Navbar";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";

const ICE = { iceServers: [{ urls: "stun:stun.l.google.com:19302" }] };

export default function SessionRoom() {
  const { id: sessionIdParam } = useParams();
  const [params] = useSearchParams();
  const appointmentId = params.get("appt");
  const navigate = useNavigate();
  const { user } = useAuth();

  const [session, setSession] = useState(null);
  const [error, setError] = useState("");
  const [callError, setCallError] = useState("");
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [callState, setCallState] = useState("idle"); // idle | connecting | live
  const [muted, setMuted] = useState(false);
  const [camOff, setCamOff] = useState(false);

  const localVideo = useRef(null);
  const remoteVideo = useRef(null);
  const pcRef = useRef(null);
  const socketRef = useRef(null);
  const streamRef = useRef(null);
  const sessionRef = useRef(null);
  const pendingIce = useRef([]);
  const lastIdRef = useRef(null);
  const chatEnd = useRef(null);

  // resolve session (may only have appointmentId on first load)
  useEffect(() => {
    const load = async () => {
      try {
        const s = sessionIdParam && sessionIdParam !== ""
          ? await api.getSession(sessionIdParam)
          : await api.getSessionByAppointment(appointmentId);
        setSession(s.session);
        sessionRef.current = s.session;
      } catch (err) {
        setError(err.payload?.message || "This session isn't available yet.");
      }
    };
    load();
  }, [sessionIdParam, appointmentId]);

  useEffect(() => { sessionRef.current = session; }, [session]);

  // poll chat only while the session is live (slow, with backoff on errors)
  useEffect(() => {
    if (!session?.id || session.status !== "live") return;
    const sid = session.id;
    let cancelled = false;
    let timer;
    let delay = 3000;

    const poll = async () => {
      try {
        const res = await api.getMessages(sid, lastIdRef.current);
        const msgs = Array.isArray(res) ? res : (res?.messages || []);
        if (msgs.length) {
          lastIdRef.current = msgs[msgs.length - 1].id;
          setMessages((prev) => {
            const seen = new Set(prev.map((m) => m.id));
            return [...prev, ...msgs.filter((m) => !seen.has(m.id))];
          });
        }
        delay = 3000;
      } catch (e) {
        delay = Math.min(delay * 2, 30000);
      }
      if (!cancelled) timer = setTimeout(poll, delay);
    };

    poll();
    return () => { cancelled = true; clearTimeout(timer); };
  }, [session?.id, session?.status]);

  useEffect(() => { chatEnd.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const startSession = async () => {
    await api.startSession(session.id);
    setSession((s) => ({ ...s, status: "live" }));
  };

  // stops media + socket. Touches refs only (no setState) so it is safe in unmount cleanup.
  const cleanupCall = () => {
    pcRef.current?.close();
    pcRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (socketRef.current) {
      socketRef.current.emit("leave_session", { session_id: sessionRef.current?.id });
      socketRef.current.disconnect();
      socketRef.current = null;
    }
    pendingIce.current = [];
  };

  const endSession = async () => {
    await api.endSession(session.id);
    cleanupCall();
    setCallState("idle");
    setSession((s) => ({ ...s, status: "ended" }));
  };

  const send = async () => {
    if (!draft.trim()) return;
    const body = draft;
    setDraft("");
    const { message } = await api.sendMessage(session.id, body);
    setMessages((prev) => (prev.some((m) => m.id === message.id) ? prev : [...prev, message]));
  };

  // ---- WebRTC for video/audio modes ----
  const getMedia = async () => {
    const wantVideo = session.mode === "video";
    try {
      return await navigator.mediaDevices.getUserMedia({ video: wantVideo, audio: true });
    } catch (e) {
      console.warn("[call] getUserMedia failed:", e.name, e.message);
      if (wantVideo) {
        // camera may be busy (e.g. used by another browser) - fall back to audio only
        const audioOnly = await navigator.mediaDevices.getUserMedia({ video: false, audio: true });
        setCamOff(true);
        setCallError("Camera unavailable (it may be in use by another app). Joined with audio only.");
        return audioOnly;
      }
      throw e;
    }
  };

  const startCall = async () => {
    if (!session || session.mode === "text" || pcRef.current) return;
    setCallError("");
    setCallState("connecting");

    // 1) media first
    let stream;
    try {
      stream = await getMedia();
    } catch (e) {
      setCallError(`Could not access microphone/camera: ${e.name}. Check browser permissions and close other apps using them.`);
      setCallState("idle");
      return;
    }
    streamRef.current = stream;
    if (localVideo.current) localVideo.current.srcObject = stream;

    // 2) peer connection
    const pc = new RTCPeerConnection(ICE);
    pcRef.current = pc;
    stream.getTracks().forEach((t) => pc.addTrack(t, stream));
    if (session.mode === "video" && stream.getVideoTracks().length === 0) {
      pc.addTransceiver("video", { direction: "recvonly" }); // still receive the other person's video
    }
    pc.ontrack = (e) => {
      if (remoteVideo.current) remoteVideo.current.srcObject = e.streams[0];
      setCallState("live");
    };
    pc.onconnectionstatechange = () => {
      console.log("[call] connection state:", pc.connectionState);
      if (pc.connectionState === "connected") setCallState("live");
      if (pc.connectionState === "failed") {
        setCallError("Connection failed. Both people should leave and join the call again.");
        setCallState("connecting");
      }
    };

    const sid = session.id;
    const isCaller = user.role !== "therapist"; // the client always creates the offer
    console.log("[call] role:", user.role, "isCaller:", isCaller);

    const makeOffer = async () => {
      console.log("[call] creating offer");
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      socketRef.current?.emit("signal", { session_id: sid, data: { sdp: offer } });
    };

    const flushIce = async () => {
      while (pendingIce.current.length) {
        const c = pendingIce.current.shift();
        try { await pc.addIceCandidate(c); } catch { /* ignore */ }
      }
    };

    pc.onicecandidate = (e) => {
      if (e.candidate) socketRef.current?.emit("signal", { session_id: sid, data: { candidate: e.candidate } });
    };

    // 3) socket LAST, with every handler registered before it can connect
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:5000";
    const socket = io(apiUrl, { withCredentials: true });
    socketRef.current = socket;

    socket.on("connect", () => {
      console.log("[call] socket connected, joining session");
      socket.emit("join_session", { session_id: sid });
    });
    socket.on("connect_error", (err) => {
      console.error("[call] socket connect_error:", err.message);
      setCallError("Could not reach the call server. Try signing in again.");
    });
    socket.on("error_message", ({ message }) => setCallError(message || "You can't join this session."));

    // other person joined after me
    socket.on("peer_joined", () => {
      console.log("[call] peer_joined");
      if (isCaller) makeOffer();
    });
    // other person was already in the room when I joined
    socket.on("peer_present", () => {
      console.log("[call] peer_present");
      if (isCaller) makeOffer();
    });

    socket.on("signal", async ({ data }) => {
      try {
        if (data.sdp) {
          console.log("[call] got", data.sdp.type);
          await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
          await flushIce();
          if (data.sdp.type === "offer") {
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);
            socket.emit("signal", { session_id: sid, data: { sdp: answer } });
          }
        } else if (data.candidate) {
          if (pc.remoteDescription) {
            try { await pc.addIceCandidate(new RTCIceCandidate(data.candidate)); } catch { /* ignore */ }
          } else {
            pendingIce.current.push(new RTCIceCandidate(data.candidate)); // queue until offer/answer is applied
          }
        }
      } catch (err) {
        console.error("[call] signal handling error:", err);
      }
    });

    socket.on("peer_left", () => setCallState("connecting"));
  };

  useEffect(() => () => cleanupCall(), []); // cleanup on unmount (no setState here)

  const toggleMute = () => { streamRef.current?.getAudioTracks().forEach((t) => (t.enabled = muted)); setMuted((m) => !m); };
  const toggleCam = () => { streamRef.current?.getVideoTracks().forEach((t) => (t.enabled = camOff)); setCamOff((c) => !c); };

  if (error) return <Shell><div className="glass rounded-4xl p-8 text-center text-rose-600 shadow-soft">{error}</div></Shell>;
  if (!session) return <Shell><div className="text-ink-soft">Loading session…</div></Shell>;

  return (
    <Shell>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold">Session with {session.counterpart_name}</h1>
          <p className="text-sm text-ink-soft capitalize">{session.mode} · {session.status}</p>
        </div>
        {session.status !== "ended" && (
          session.status === "live"
            ? <button onClick={endSession} className="rounded-full bg-rose-500 px-5 py-2.5 text-sm font-semibold text-white">End session</button>
            : <button onClick={startSession} className="rounded-full bg-gradient-to-r from-lavender-deep to-lavender px-5 py-2.5 text-sm font-semibold text-white">Start session</button>
        )}
      </div>

      {session.status === "ended" && (
        <div className="glass rounded-4xl p-8 text-center shadow-soft">
          <div className="mb-2 text-3xl">✅</div>
          <p className="mb-4 text-ink-soft">This session has ended.</p>
          <button onClick={() => navigate("/appointments")} className="rounded-full bg-ink px-5 py-2.5 text-sm font-semibold text-white">Back to appointments</button>
        </div>
      )}

      {session.status === "live" && (
        <div className={`grid gap-5 ${session.mode === "text" ? "" : "md:grid-cols-[1.3fr_1fr]"}`}>
          {session.mode !== "text" && (
            <div className="glass overflow-hidden rounded-4xl p-4 shadow-soft">
              <div className="relative aspect-video overflow-hidden rounded-3xl bg-ink">
                <video ref={remoteVideo} autoPlay playsInline className="h-full w-full object-cover" />
                <video ref={localVideo} autoPlay playsInline muted className="absolute bottom-3 right-3 h-24 w-32 rounded-xl border-2 border-white object-cover" />
                {callState !== "live" && (
                  <div className="absolute inset-0 grid place-items-center bg-ink/60 px-4 text-center text-white">
                    {callState === "idle" ? (
                      <div>
                        <button onClick={startCall} className="rounded-full bg-white px-5 py-2.5 text-sm font-semibold text-ink">Join {session.mode} call</button>
                        {callError && <p className="mt-3 text-xs text-rose-200">{callError}</p>}
                      </div>
                    ) : (
                      <div>
                        <span>Connecting…</span>
                        {callError && <p className="mt-3 text-xs text-rose-200">{callError}</p>}
                      </div>
                    )}
                  </div>
                )}
              </div>
              {callState === "live" && (
                <div className="mt-3 flex flex-col items-center gap-2">
                  {callError && <p className="text-xs text-ink-soft">{callError}</p>}
                  <div className="flex justify-center gap-3">
                    <button onClick={toggleMute} className="rounded-full bg-white/70 px-4 py-2 text-xs font-semibold">{muted ? "Unmute" : "Mute"}</button>
                    {session.mode === "video" && <button onClick={toggleCam} className="rounded-full bg-white/70 px-4 py-2 text-xs font-semibold">{camOff ? "Camera on" : "Camera off"}</button>}
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="glass flex h-[480px] flex-col rounded-4xl p-4 shadow-soft">
            <div className="flex-1 space-y-2 overflow-y-auto px-1">
              {messages.map((m) => (
                <div key={m.id} className={`max-w-[80%] rounded-2xl px-3 py-2 text-sm ${m.mine ? "ml-auto bg-lavender-deep text-white" : "bg-white/80 text-ink"}`}>
                  {m.body}
                </div>
              ))}
              <div ref={chatEnd} />
            </div>
            <div className="mt-3 flex gap-2">
              <input value={draft} onChange={(e) => setDraft(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()}
                placeholder="Type a message…" className="flex-1 rounded-2xl bg-white/70 px-4 py-2.5 text-sm outline-none" />
              <button onClick={send} className="rounded-2xl bg-ink px-4 py-2.5 text-sm font-semibold text-white">Send</button>
            </div>
          </div>
        </div>
      )}
    </Shell>
  );
}

function Shell({ children }) {
  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="mx-auto max-w-4xl px-6 py-10">{children}</div>
    </div>
  );
}