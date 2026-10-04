# API Reference

Base URL: `http://localhost:5000` — all routes prefixed `/api`. Auth uses httpOnly
cookies; write requests (`POST`/`PUT`/`DELETE`) need an `X-CSRF-TOKEN` header
matching the `csrf_access_token` cookie (see `frontend/src/services/api.js`).

## Auth
| Method | Path | Notes |
|---|---|---|
| POST | `/api/auth/register` | `role: "user"` or `"therapist"`. Therapist registration requires qualification, registration number, specializations, languages. Admins can't self-register. |
| POST | `/api/auth/login` | Body includes `portal: "user" \| "therapist" \| "admin"` — logging in from the wrong portal is rejected. |
| POST | `/api/auth/logout`, `/refresh` | |
| GET | `/api/auth/me` | Returns the current user + a fresh CSRF token |
| POST | `/api/auth/verify-email`, `/forgot-password`, `/reset-password`, `/change-password` | |

## Users
| GET/PUT | `/api/users/me/profile` | Display name, privacy mode, language, concerns |
| DELETE | `/api/users/me` | Erases journal/safety-plan/check-in data, anonymises the account (requires password) |

## Therapists (public)
| GET | `/api/therapists` | Filters: `specialization`, `language`, `max_price`, `gender`, `mode`, `q` (search) |
| GET | `/api/therapists/:id` | Includes recent reviews |
| GET | `/api/therapists/:id/slots?days=7` | Real bookable slots generated from availability minus existing bookings |
| POST | `/api/matching` | Preference-based, transparent scoring with plain-language reasons |

## Appointments (client)
| GET/POST | `/api/appointments` | POST checks slot availability + a DB-level unique constraint |
| GET/PUT/DELETE | `/api/appointments/:id` | `PUT` actions: `cancel`, `reschedule`, `share_summary` |
| POST | `/api/appointments/:id/review` | Only after `status=completed` |

## AI
| POST | `/api/check-in` | Returns emotion + risk **tier** (never the raw score) |
| GET | `/api/check-in/history` | |
| POST | `/api/check-in/summary` | Private pre-session summary; only shared if the client opts in on the appointment |

## Journal / Safety (private, owner-only)
| GET/POST/PUT/DELETE | `/api/journal`, `/api/journal/:id` | |
| GET/PUT | `/api/safety-plan` | |

## Wellness
| GET | `/api/progress` | Mood trend + emotion counts from real logged data |
| GET | `/api/recovery`, POST `/recovery/complete`, `/recovery/reset` | 7-day sequential journey |

## Payments
| GET | `/api/payments/config` | `{mode: "test" \| "razorpay"}` |
| POST | `/api/payments/create-order` | |
| POST | `/api/payments/verify` | Razorpay only — HMAC-SHA256 signature check |
| POST | `/api/payments/test-confirm` | Test mode only; rejected once real keys are configured |

## Sessions & chat (participant-only, enforced server-side)
| GET | `/api/sessions/by-appointment/:id`, `/api/sessions/:id` | |
| POST | `/api/sessions/:id/start`, `/end` | |
| PUT | `/api/sessions/:id/notes` | Therapist only |
| GET/POST | `/api/messages/:sessionId` | Poll with `?after=<id>` |
| Socket.IO | `join_session`, `signal`, `leave_session` | WebRTC signalling relay only — media is peer-to-peer |

## Therapist portal (role=therapist)
| GET/PUT | `/api/therapist/me` | |
| GET/PUT | `/api/therapist/availability` | Weekly windows in IST |
| GET | `/api/therapist/overview` | Today's schedule + counts |
| GET | `/api/therapist/appointments?status=` | |
| POST | `/api/therapist/appointments/:id/respond` | `accept \| decline \| complete \| no_show` |
| GET | `/api/therapist/appointments/:id/pre-session` | Only returns data if the client opted in |
| GET | `/api/therapist/earnings` | |

## Admin portal (role=admin)
| GET | `/api/admin/analytics` | Totals + 14-day time series + session-type breakdown |
| GET | `/api/admin/system` | DB/email/payments health check |
| GET | `/api/admin/users?role=`, POST `/:id/suspend`, `/activate` | |
| GET | `/api/admin/therapists?status=`, POST `/:id/verify` | |
| GET | `/api/admin/appointments`, `/payments`, POST `/payments/:id/mark-refunded` | |
| GET/POST/PUT/DELETE | `/api/admin/resources` | |
| GET | `/api/admin/reviews`, POST `/:id/flag` | |
| GET | `/api/admin/audit-logs` | |

## Health
| GET | `/api/health` | `{"status": "ok"}` |
