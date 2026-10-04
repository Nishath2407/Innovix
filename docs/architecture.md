# SafeVoice Architecture

## Technology choices

| Layer | Choice | Why |
|---|---|---|
| Backend framework | Flask | Blueprint architecture maps cleanly onto the app's domains (auth, therapists, payments, etc.); lightweight enough to keep the AI/service layers explicit rather than hidden behind framework magic. |
| ORM | SQLAlchemy + Flask-Migrate | Mature migration tooling, works identically against SQLite (dev) and PostgreSQL (prod). |
| Auth | JWT in httpOnly cookies + CSRF double-submit | Avoids storing tokens in localStorage (XSS-exposed) while still working for a decoupled SPA frontend. |
| Real-time chat | Flask-SocketIO | Runs in the same process as the REST API for now; can be split into a dedicated service later without changing the message model. |
| Video/audio | WebRTC (client-side, signaling via Socket.IO) | No third-party video vendor lock-in; signaling reuses the existing socket connection. |
| Frontend | React + Vite + Tailwind | Fast dev loop, utility CSS keeps the design token system (see frontend-design brief) enforceable via `tailwind.config.js`. |
| AI | HuggingFace DistilRoBERTa emotion model | Wrapped in a service with a keyword fallback so the app degrades gracefully rather than crashing when the model can't be downloaded. |
| Payments | Razorpay | Widely used in India; server-side HMAC verification, no secret key ever sent to the client. |

## Database relationships (key ones)

- `User` 1—1 `UserProfile` (auth identity vs. display identity, intentionally split)
- `User` 1—1 `Therapist` (a therapist IS a user with role="therapist", plus a therapist-specific profile row)
- `Therapist` 1—N `TherapistCredential`, `TherapistSpecialization`, `TherapistLanguage`, `TherapistAvailability`
- `User` + `Therapist` → N `Appointment` (unique constraint on `(therapist_id, scheduled_start)` prevents double-booking)
- `Appointment` 1—1 `TherapySession` (session room state, separate from the booking record)
- `TherapySession` 1—N `Message`
- `User` 1—N `Payment`, `JournalEntry`, `EmotionResult`, `RiskAssessment`, `Notification`
- `User` 1—1 `SafetyPlan` 1—N `TrustedContact`
- `Therapist` 1—N `Review` (one per completed `Appointment`, enforced via unique constraint)

## What changed from the original MVP

The client, therapist, and admin experiences are now three real portals rather
than one app with placeholder screens: therapists apply and get verified before
they're bookable, availability is real (slots are generated, not hand-typed),
bookings go through an accept/decline step, payments have a safe local test mode
that becomes real Razorpay the moment keys are set, and sessions support actual
WebRTC video/audio alongside text chat. Matching, progress charts, and the 7-day
recovery journey are also fully wired to real data now.

## API modules

Each Flask blueprint maps 1:1 to a product domain: `auth`, `users`,
`therapists`, `appointments`, `sessions`, `chat`, `ai`, `payments`, `journal`,
`safety`, `resources`, `notifications`, `admin`. See `README.md` for the full
endpoint list, or `app/__init__.py` for the registered URL prefixes.

## Security-sensitive areas (extra review priority)

1. `app/payments/routes.py` — HMAC signature verification; must never trust
   client-reported payment status.
2. `app/models/user.py` / `app/models/therapist.py` — the email/display-name
   split; any future query joining `Therapist` to `User.email` is a privacy
   regression.
3. `app/ai/risk_service.py` + `RiskAssessment.to_user_facing_dict()` — raw
   scores must never reach the frontend.
4. `app/journal/routes.py`, `app/safety/routes.py` — ownership checks on
   every read/write.
5. `app/utils/decorators.py` — the shared enforcement point for role and
   ownership checks; changes here affect every blueprint.

## Phase status

The core foundation — architecture, auth, database, therapist discovery,
appointment booking with double-booking prevention — is functionally complete
and tested. Payments and the AI check-in also have working backend
implementations. Still open: the live video/audio session UI, progress
charts, recovery content, the full safety hub content pages, admin/therapist
dashboards, accessibility auditing, load testing, and production deployment —
see the README's "What's built vs. what's next" section.
