# SafeVoice — Project Overview & Presentation Guide

**Professional support, wherever you are.**

---

## 1. What is SafeVoice?

SafeVoice is a privacy-first online mental-health platform. It connects people
with licensed therapists through video, audio, or text sessions — removing
the usual barriers to therapy: commute, scheduling, discomfort with in-person
visits, and privacy concerns.

**What it is not:** an AI therapist, or a generic booking website. AI is used
only to help users check in emotionally and prepare for sessions — it never
diagnoses. A licensed human therapist always provides the actual care.

**Core differentiators:**
| Feature | What it means |
|---|---|
| Flexible modes | User picks video, audio, or text — never forced into video |
| Privacy Mode | Therapist sees an anonymous display name, never the user's email |
| Quick Exit | One click leaves sensitive screens instantly |
| Smart matching | Transparent, explained therapist recommendations |
| AI check-in | Supportive emotional check-in, never a diagnosis |
| Women's Safety Hub | Dedicated resources: DV support, harassment, safety planning |

---

## 2. Project Status (be upfront about this when presenting)

This is a **working MVP built in phases**, not a finished product — and that's
by design. The plan from the start was to build the core foundation solidly
first (auth, database, booking, payments, AI check-in) and add polish and
remaining screens incrementally, rather than rushing every feature and ending
up with something fragile. See `docs/architecture.md` for the phase breakdown.

**✅ Built, working, and tested (11/11 automated tests passing):**
- Full authentication system (register, login, logout, email verification,
  password reset) with UUID-based identity
- Therapist discovery with filtering (specialization, language, price, gender)
- Appointment booking with **real double-booking prevention** (enforced at
  the database level, not just in application code)
- AI-assisted emotional check-in (emotion classification + risk tiering)
- Private journal (strict ownership enforcement)
- Safety plan with trusted contacts
- Razorpay payment order creation + cryptographic signature verification
- Real-time chat scaffolding (Socket.IO)
- Admin analytics and therapist verification endpoints
- A polished, published landing page

**🚧 Deliberately not built yet** (shown as honest "Coming soon" screens,
never faked): live WebRTC video room UI, the matching-algorithm UI, calendar
view, emotional-progress charts, therapist/admin dashboards, multilingual UI
wiring (translation files exist, aren't wired to components yet).

---

## 3. Complete Folder Structure

```
safevoice/
│
├── frontend/                        React application (what users interact with)
│   ├── src/
│   │   ├── pages/                   One file per screen (Landing, Login, Dashboard, etc.)
│   │   ├── components/              Reusable pieces (Navbar, ExitSafelyButton, ProtectedRoute)
│   │   ├── context/                 AuthContext.jsx — holds "who is logged in" app-wide
│   │   ├── services/                api.js — the ONLY place that talks to the backend
│   │   ├── locales/                 en.json, hi.json, te.json — translation strings
│   │   ├── App.jsx                  All page routes defined here
│   │   └── main.jsx                 React entry point
│   ├── package.json                 Frontend dependencies list
│   ├── vite.config.js               Dev server / build tool config
│   ├── tailwind.config.js           Design system (colors, fonts) as code
│   └── Dockerfile
│
├── backend/                         Flask API (the "brain" — business logic, database, security)
│   ├── app/
│   │   ├── models/                  Database table definitions (20 tables)
│   │   ├── auth/                    Register, login, logout, password reset
│   │   ├── users/                   User profile management
│   │   ├── therapists/              Therapist discovery & filtering
│   │   ├── appointments/            Booking, rescheduling, cancellation
│   │   ├── sessions/                Live therapy session room lifecycle
│   │   ├── chat/                    Real-time text messaging
│   │   ├── ai/                      Emotion classification + risk scoring
│   │   ├── payments/                Razorpay integration
│   │   ├── journal/                 Private journaling
│   │   ├── safety/                  Safety plan & trusted contacts
│   │   ├── resources/               Curated mental-health resources
│   │   ├── notifications/           In-app notifications
│   │   ├── admin/                   Analytics, therapist verification
│   │   ├── utils/                   Shared authorization decorators
│   │   ├── __init__.py              App factory — wires everything together
│   │   ├── config.py                Environment-based settings
│   │   └── extensions.py            Database, JWT, CORS, etc. — set up once
│   ├── migrations/                  Database version history (Flask-Migrate/Alembic)
│   ├── tests/                       Automated test suite
│   ├── requirements.txt             Python dependencies list
│   ├── run.py                       Backend entry point (start command)
│   └── .env.example                 Template for secret configuration
│
├── scripts/
│   └── seed_database.py             One-time script: fills the DB with 10 sample therapists
│
├── docs/                            Written documentation
│   ├── architecture.md              Technology choices & reasoning
│   ├── api.md                       Every API endpoint, documented
│   ├── privacy.md                   What data is collected and why
│   ├── security.md                  Security measures implemented
│   └── deployment.md                Step-by-step production deployment guide
│
├── docker-compose.yml                Runs backend + frontend + database together, one command
├── README.md                         Setup instructions (the file you asked for — below)
└── .gitignore                        Keeps secrets and junk files out of version control
```

---

## 4. Technology Stack — What and Why

### Backend
| Technology | Role | Why this choice |
|---|---|---|
| **Python + Flask** | Web framework | Lightweight; its "Blueprint" system maps cleanly onto SafeVoice's modules (auth, payments, journal, etc. each get their own folder) |
| **SQLAlchemy** | ORM (talks to the database using Python objects instead of raw SQL) | Prevents SQL-injection by design; works identically against SQLite and PostgreSQL |
| **Flask-Migrate (Alembic)** | Database version control | Every schema change is tracked, like Git but for database structure |
| **PostgreSQL** (production) / **SQLite** (local dev) | Database | Postgres is production-grade and handles concurrent users; SQLite needs zero setup for local development |
| **Flask-JWT-Extended** | Authentication tokens | Issues secure login tokens stored in cookies the browser's JavaScript can't read (blocks a common attack) |
| **Flask-Bcrypt** | Password hashing | Industry-standard one-way password scrambling — even we can't see a user's real password |
| **Flask-SocketIO** | Real-time communication | Powers live chat during therapy sessions without the browser needing to constantly ask "any new messages?" |
| **Razorpay SDK** | Payments | India-focused payment gateway; every payment is verified server-side with an HMAC signature check so no one can fake a "payment successful" state |
| **HuggingFace Transformers (DistilRoBERTa)** | AI emotion detection | Reads a user's check-in text and detects emotions like anxiety or sadness — with a safe fallback if the AI model isn't available |
| **Flask-Limiter** | Rate limiting | Stops attackers from brute-forcing passwords by capping login attempts per hour |

### Frontend
| Technology | Role | Why this choice |
|---|---|---|
| **React** | UI library | Industry standard; breaks the interface into reusable components |
| **Vite** | Build tool / dev server | Much faster page reloads during development than older tools |
| **React Router** | Page navigation | Lets the app feel like multiple pages without full page reloads |
| **Tailwind CSS** | Styling | Design tokens (SafeVoice's colors/fonts) are defined once in config and reused everywhere — keeps the look consistent |
| **Socket.IO Client** | Real-time chat | Talks to the backend's Flask-SocketIO for live messaging |

### Infrastructure
| Technology | Role |
|---|---|
| **Docker / docker-compose** | Packages backend + frontend + database so they run identically on any machine with one command |
| **Gunicorn + Eventlet** | Production-grade server that actually runs the Flask app (Flask's built-in server is dev-only) |

---

## 5. Complete Workflow — How a Request Actually Travels

**Example: a user books a therapy session.**

```
1. User clicks "Find a Therapist" on the React frontend (localhost:5173)
        ↓
2. React calls api.listTherapists() → services/api.js sends a
   fetch request to the Flask backend (localhost:5000/api/therapists)
        ↓
3. Flask's therapists blueprint (app/therapists/routes.py) receives it,
   queries the PostgreSQL/SQLite database through SQLAlchemy models
        ↓
4. Database returns matching therapist rows → Flask converts them to JSON
   (carefully excluding the therapist's linked User.email — privacy by design)
        ↓
5. React receives the JSON and renders therapist cards
        ↓
6. User picks a time slot and clicks "Book"
        ↓
7. React sends POST /api/appointments with therapist_id + time
        ↓
8. Flask checks: is this time slot already taken? (a UNIQUE database
   constraint on therapist_id + time physically prevents double-booking,
   even under race conditions)
        ↓
9. Appointment created with status "pending" → user is sent to pay
        ↓
10. React calls POST /api/payments/create-order → Flask talks to Razorpay's
    servers → returns an order ID (never the secret key) to the browser
        ↓
11. Razorpay's own checkout UI handles the actual card/UPI payment
        ↓
12. Razorpay sends back a payment ID + signature → React sends these to
    POST /api/payments/verify → Flask re-computes the signature using the
    secret key (which never left the server) and confirms it matches
        ↓
13. Only after that cryptographic match does Flask mark the appointment
    "confirmed" — the backend never just trusts "the frontend said it worked"
```

This same pattern (frontend asks → Flask authorizes & validates → database →
JSON back → React renders) repeats for every feature: journaling, the AI
check-in, safety plans, everything.

### Authentication flow specifically
```
Register → password hashed with bcrypt → stored in `users` table
Login → password checked → JWT tokens issued → stored as httpOnly cookies
         (JavaScript literally cannot read these cookies — blocks XSS token theft)
Every protected request → Flask checks: (1) valid token? (2) correct role?
         (3) does this user actually own the resource they're asking for?
```

---

## 6. Why You Run This in Multiple Terminals

This is a **client-server architecture** — two separate programs that must
both be *running continuously* at the same time and talk to each other over
the network (even though "the network" here is just your own laptop).

| Terminal | What runs | Why it must stay open |
|---|---|---|
| **Terminal 1** | `python run.py` (Flask backend, port 5000) | This is a live server process. The moment you close this terminal or hit Ctrl+C, the API stops responding and the frontend breaks. |
| **Terminal 2** | `npm run dev` (React frontend, port 5173) | Also a live, continuously-running dev server. It watches your files for changes and hot-reloads the browser. |
| **Terminal 3** (one-time use, not continuous) | `python scripts/seed_database.py` | This is a **script**, not a server — it runs once, adds 10 sample therapist profiles to the database, and exits. You can technically run it in Terminal 1 *before* starting `run.py`, but most people open a third terminal so they don't have to stop and restart the backend to do it. |

**The short version:** a server that stops running is a server that stops
working — so the backend and frontend each need their own terminal to stay
alive simultaneously, and any one-off command (seeding, running tests,
database migrations) is cleanest in a separate window so it doesn't
interrupt either running server.

**Simplification available:** running `docker-compose up` starts the
backend, frontend, *and* PostgreSQL together in a single terminal — useful
for a demo, though the two-terminal setup is more common for active
development since you can see each service's logs separately and restart
just one without affecting the other.

---

## 7. Database — The 20 Tables and How They Relate

```
users ──1:1── user_profiles          (auth identity kept separate from display identity)
users ──1:1── therapists ──1:N── therapist_credentials
                          ├──1:N── therapist_specializations
                          ├──1:N── therapist_languages
                          └──1:N── therapist_availability

users + therapists ──1:N── appointments  (UNIQUE constraint prevents double-booking)
appointments ──1:1── therapy_sessions ──1:N── messages

users ──1:N── payments
users ──1:N── journal_entries          (private — owner-only access enforced in code)
users ──1:N── emotion_results ──1:N── risk_assessments
users ──1:1── safety_plans ──1:N── trusted_contacts
users ──1:N── notifications

therapists ──1:N── reviews
(standalone) resources, audit_logs
```

**Key design decision:** `users` (which holds the email) and `user_profiles`
(which holds the display name shown to therapists) are deliberately two
separate tables. This makes it structurally hard to accidentally leak a
user's email to a therapist-facing screen — the email simply isn't in the
data being queried for that purpose.

---

## 8. Security Highlights (good talking points for a presentation)

1. **Passwords** — hashed with bcrypt, never stored or logged in plain text
2. **Tokens** — delivered as httpOnly cookies (invisible to JavaScript,
   blocking a major class of attack)
3. **CSRF protection** — every write request requires a matching token
4. **Authorization** — every protected endpoint checks three things: valid
   login, correct role, and actual ownership of the resource
5. **Payment integrity** — Razorpay payments are verified with a
   cryptographic signature check on the server; the frontend's word is
   never trusted alone
6. **No raw risk scores exposed** — the AI's internal 0–100 risk number
   never reaches the browser; only a translated, supportive message does
7. **Database-level double-booking prevention** — enforced by the database
   itself, not just application logic, so it holds even under simultaneous
   requests

---

## 9. Testing

`backend/tests/test_core.py` — 11 automated tests, all currently passing:
health check, UUID identity generation, duplicate-registration rejection,
weak-password rejection, wrong-password login rejection, auth-required
enforcement, confirmation that a therapist's card never contains their
email, double-booking prevention, journal auth requirement, and
admin-role enforcement.

Run them yourself: `cd backend && pytest tests/ -v`

---

## 10. Setup Instructions (README)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in real secret values
python run.py                   # → http://localhost:5000
```

### Seed demo data (separate terminal, one-time)
```bash
cd backend
python ../scripts/seed_database.py
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev                     # → http://localhost:5173
```

### Everything at once (alternative)
```bash
docker-compose up --build
```

### Health check
```
GET http://localhost:5000/api/health → {"status": "ok"}
```

---

## 11. Suggested Presentation Flow

If you're demoing this to someone, a natural order is:

1. **Show the published landing page** — the "why does this matter" pitch
2. **Register a new account** → point out the email-vs-display-name split
3. **Browse therapists** → filter by specialization/language → open a profile
4. **Try the private check-in** → show it returns a supportive message, not
   a diagnosis, and explain the raw risk score never leaves the server
5. **Add a journal entry** → explain the ownership check in the code
6. **Walk through the folder structure** → this document's section 3
7. **End with the roadmap** — what's built vs. what's next, so it's clear
   this is an honest, in-progress MVP, not a finished product
