# Security

## Authentication & sessions
- Passwords hashed with bcrypt (`Flask-Bcrypt`), never stored or logged in
  plaintext.
- JWT access/refresh tokens delivered via httpOnly, SameSite cookies —
  not accessible to JavaScript, mitigating XSS token theft.
- CSRF double-submit cookie pattern required on all state-changing requests.
- `SESSION_COOKIE_SECURE` / `JWT_COOKIE_SECURE` forced true in production.

## Authorization
Every protected endpoint enforces, in order: (1) valid JWT via
`login_required`/`role_required`/`jwt_required`, (2) correct role where
applicable, (3) resource ownership (checked inline — e.g. journal entries,
safety plans, sessions, messages all verify `resource.user_id == current_user`
or admin override). See `app/utils/decorators.py`.

## Input handling
- Registration/login validate email format and password length server-side
  (never trust client-side validation alone).
- All request bodies parsed with `get_json(silent=True)` and defensively
  defaulted — malformed JSON never raises an unhandled exception.
- SQLAlchemy ORM used throughout — no raw string-interpolated SQL, which
  is the primary SQL-injection defense.

## Payments
Razorpay signature verified server-side with `hmac.compare_digest` (constant-time
comparison) over `order_id|payment_id` using the server-only secret key. The
secret key is never sent to the frontend; only the publishable key ID is.

## Rate limiting
`Flask-Limiter` applied to registration (10/hr), login (15/hr), and password
reset requests (5/hr) to slow credential-stuffing and enumeration attacks.

## Data minimization / logging
Sensitive fields (passwords, tokens, journal/therapy content, payment
secrets) are never written to application logs — see the explicit comments
in `app/auth/routes.py` ("email intentionally not logged").

## Admin/oversight boundary
Admin endpoints (`app/admin/routes.py`) return accounts, bookings, payments, and
aggregate analytics — never journal entries, safety plans, or check-in text. This
is enforced by what the queries select, not by hiding fields after the fact, and
is checked directly in `test_admin_never_sees_private_content`.

## Known gaps for production hardening (tracked, not hidden)
- Email verification/password reset tokens are generated and, if `MAIL_SERVER`
  is left blank, printed to the backend console instead of emailed — fine for
  development, but set real SMTP credentials before real users register.
- File upload handling (therapist credentials) has a `file_path` column but
  no upload endpoint yet — implement with strict type/size validation and
  private storage before enabling in production.
- Full penetration testing and a dependency vulnerability scan should happen
  before real user data is processed.
