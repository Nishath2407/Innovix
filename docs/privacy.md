# Privacy

SafeVoice minimizes unnecessary personal-data exposure and does not expose a
user's email identity to therapists by default. This is not a claim of
complete anonymity — see limitations below.

## What's collected and why
- **Email** — authentication and account recovery only. Stored on `User`,
  never joined into therapist-facing queries or responses.
- **Display name** — stored on `UserProfile`, shown to therapists instead of
  email (default: `Anonymous User #XXXX`).
- **Journal entries, safety plans** — private by default; only the owning
  user's requests can read/write them (enforced in code, not just UI).
- **AI check-in text and results** — private by default (`is_shared_with_therapist`
  defaults to `False`); a user must explicitly opt to share.
- **Payment records** — required for legal/operational reasons (refunds,
  disputes, tax); not exposed to therapists.

## What therapists can see
Display name, session mode/time, and — only if the user explicitly shares —
an AI-generated pre-session summary. Never: email, journal, safety plan,
unrelated account data.

## Limitations (stated plainly, not hidden)
- SafeVoice is **not untraceable**. Account/payment records exist.
- The **Quick Exit** button leaves sensitive screens instantly but cannot
  clear browser history, ISP logs, or employer/network monitoring.
- Admins can see aggregate analytics and moderation-relevant data, not raw
  therapy conversation content, by design (see `docs/architecture.md`
  security-sensitive areas).

## Legal review required before production launch
This document and the in-app `/privacy` page are product-level explanations,
not a substitute for a legally reviewed privacy policy required before
handling real user data in production.
