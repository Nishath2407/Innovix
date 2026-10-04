# SafeVoice

**Professional support, wherever you are.**

A privacy-first online mental-health platform connecting people with licensed therapists
through video, audio, or text sessions — with AI used only to help users check in
emotionally and prepare, never to diagnose or replace professional care.

Three separate portals, one platform:
- **Client app** — discover therapists, get a transparent match, book and pay for sessions, journal privately, track progress.
- **Therapist portal** — apply, get verified, manage availability, accept/decline requests, run sessions, track earnings.
- **Admin portal** — monitor the whole platform: analytics, user/therapist management, payments, audit logs, resources.

---

## What's actually working

This isn't a mockup — every flow below runs end to end against a real database and is covered by automated tests (39 passing).

- **Auth for three portals** with role-based login (`/login`, `/therapist/login`, `/admin/login`), UUID identity kept separate from email, password reset, account deletion that actually erases private data.
- **Real booking**, not a static list: therapists set weekly availability, the API generates actual open time slots, and a database-level constraint makes double-booking structurally impossible — not just discouraged by application code.
- **Payments** with a safe local **test mode** (no card details needed to try the full flow) that automatically becomes real Razorpay verification the moment you add live API keys — the switch is server-side, not a toggle someone could flip from the browser.
- **Therapist accept/decline workflow** — a booking isn't confirmed until the therapist accepts it. Declines and late cancellations trigger a refund queue the admin can see and close out.
- **Live sessions**: real WebRTC video/audio (peer-to-peer, signaled through the backend) plus real-time text chat — not a "coming soon" placeholder.
- **AI check-in** with emotion detection and risk tiering that never exposes a raw score to the frontend — only a supportive tier and next step.
- **Transparent matching** — every recommendation comes with plain-language reasons, not a black-box score.
- **Admin oversight** that can see accounts, bookings, and payments, but is structurally unable to see journal entries, safety plans, or check-in text — verified by an explicit test.
- **7-day recovery journey and mood/progress charts** backed by real logged data.

---

## Project Structure

```
safevoice/
│
├── frontend/                         React app — client, therapist, and admin portals
│   ├── src/
│   │   ├── pages/                    One file per screen, incl. TherapistDashboard.jsx and AdminDashboard.jsx
│   │   ├── components/               Navbar, Blobs (background), BookingModal, ProtectedRoute (role-aware), StatusPill
│   │   ├── context/                  AuthContext.jsx — tracks who's logged in and which portal
│   │   ├── services/                 api.js — every backend call lives here
│   │   ├── constants.js              Shared dropdown/chip options (concerns, languages, modes)
│   │   ├── App.jsx                   All routes, grouped by portal
│   │   └── main.jsx
│   ├── package.json / vite.config.js / tailwind.config.js
│   └── Dockerfile
│
├── backend/                          Flask API
│   ├── app/
│   │   ├── models/                   21 database tables
│   │   ├── auth/                     Registration (client + therapist application), portal-based login
│   │   ├── users/                    Profile, privacy settings, account deletion
│   │   ├── therapists/               Public discovery, slot generation, transparent matching
│   │   │   └── portal.py             Everything a logged-in therapist can do
│   │   ├── appointments/             Booking, cancellation, rescheduling, reviews
│   │   │   └── service.py            Slot generation + double-booking prevention logic
│   │   ├── sessions/                 Session lifecycle + join-window rules
│   │   │   └── realtime.py           WebRTC signalling relay (Socket.IO)
│   │   ├── chat/                     Session-scoped text messages
│   │   ├── ai/                       Emotion classification + risk scoring
│   │   ├── payments/                 Razorpay + test-mode payment handling
│   │   ├── journal/, safety/         Private-by-design user content
│   │   ├── wellness/                 Progress charts + 7-day recovery tracking
│   │   ├── resources/                Public mental-health resource library
│   │   ├── notifications/            In-app notifications
│   │   ├── admin/                    Analytics, user/therapist management, audit logs
│   │   ├── utils/                    Auth decorators, mailer (console fallback), audit logging, time helpers
│   │   ├── config.py / extensions.py / __init__.py
│   ├── migrations/                   Initialized fresh per environment (see Setup below)
│   ├── tests/                        39 tests covering all three portals
│   ├── requirements.txt / run.py / .env.example
│   └── Dockerfile
│
├── scripts/
│   └── seed_database.py              Creates an admin account + 10 verified sample therapists with real weekly availability
│
├── docs/
│   ├── architecture.md               Technology choices and reasoning
│   ├── api.md                        Every endpoint, documented
│   ├── privacy.md / security.md      What's collected, how it's protected
│   └── deployment.md                 Production deployment steps
│
├── docker-compose.yml
├── README.md
└── .gitignore
```

---

## Setup

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in real values later; defaults work for local dev

flask --app run.py db init      # one-time, first setup only
flask --app run.py db migrate -m "initial schema"
flask --app run.py db upgrade

python run.py                   # → http://localhost:5000
```

### 2. Seed sample data (a second terminal)

```bash
cd backend
python ../scripts/seed_database.py
```

This creates one admin account and 10 verified sample therapists with real weekly
availability, and **prints the login credentials once** — copy them somewhere safe.
Running it again is harmless; it won't duplicate data or reset existing passwords.

> **Why separate terminals?** The backend (`python run.py`) is a long-running server
> that must stay alive to answer requests — closing its terminal stops the API.
> `seed_database.py` is a one-time script, not a server, so it's cleanest to run in
> its own terminal rather than interrupting the running backend to do it.

### 3. Frontend (a third terminal)

```bash

cd frontend
npm install
cp .env.example .env
npm run dev                     # → http://localhost:5173
```

Visit `/login` as a client, `/therapist/login` with a seeded therapist account, or
`/admin/login` with the printed admin credentials.

### Everything at once (alternative)

```bash
docker-compose up --build
```

---

## Payments: test mode vs. live

By default (`PAYMENTS_TEST_MODE=true`, the local default), the app uses a clearly
separate **test confirmation** endpoint — no card details, no real gateway call — so
you can demo the entire booking-to-confirmation flow without a Razorpay account.
The moment `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` are set (and in production),
the app automatically switches to real Razorpay order creation and HMAC-SHA256
signature verification. This switch happens server-side; the frontend just asks
`/api/payments/config` which mode is active.

---

## Architecture

```
Client browser → React (Vite) → Flask REST API → PostgreSQL / SQLite
                              ↕ Socket.IO (WebRTC signalling + nothing else — media is peer-to-peer)
                              → Razorpay (when configured)
```

See `docs/architecture.md` for the full technology-choice reasoning and database
relationships.

---

## Security notes

- Passwords hashed with bcrypt; auth tokens delivered as httpOnly, SameSite cookies with CSRF double-submit protection.
- Every protected route checks: (1) valid login, (2) correct role for that portal, (3) actual ownership of the resource being accessed.
- A suspended account's existing login session stops working on its very next request — not just at the next login.
- Razorpay payments are verified server-side via constant-time HMAC comparison; the frontend's claim of "payment succeeded" is never trusted alone.
- Raw AI risk scores never leave the server — only a translated tier and supportive next step.
- Admin endpoints are verified (via an automated test) to be structurally incapable of returning journal entries, safety plans, or check-in text.
- A booking slot is guaranteed unique at the database level (a partial unique index), not just checked in application code — this holds even under simultaneous requests.

See `docs/security.md` for the full list.

---

## Testing

```bash
cd backend
pytest tests -v
```

39 tests across `test_auth.py` and `test_flows.py` cover: registration/login for all
three portals, therapist verification gating, double-booking prevention (including
a direct database-constraint test), the full payment → accept → session → chat →
review lifecycle, Razorpay signature verification (valid and invalid), refund
queuing on decline/cancellation, journal and safety-plan privacy (including after
account deletion), AI risk tiering, admin's inability to see private content, and
suspended-account session invalidation.

## Deployment

See `docs/deployment.md` for the Vercel (frontend) + Railway/Render (backend) +
managed PostgreSQL path, including running `flask db upgrade` and configuring
`PAYMENTS_TEST_MODE=false` with real Razorpay keys for production.
