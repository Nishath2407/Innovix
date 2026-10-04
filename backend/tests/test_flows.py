import pytest
from datetime import timedelta
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.appointment import Appointment
from app.models.payment import Payment
from app.models.therapy_session import TherapySession
from app.models.user import User
from app.models.journal_entry import JournalEntry
from app.utils.timeutils import utcnow


# ---------- therapist onboarding + verification ----------
def test_therapist_application_hidden_until_admin_approves(app, make_client, h):
    t = make_client()
    r = t.post("/api/auth/register", json=h.therapist_payload())
    assert r.status_code == 201
    h.login(t, "doc@example.com", "therapist")
    tid = t.get("/api/therapist/me").get_json()["therapist"]["id"]

    public = make_client()
    assert public.get("/api/therapists").get_json()["therapists"] == []
    assert public.get(f"/api/therapists/{tid}").status_code == 404

    admin = make_client(); h.make_admin(app, admin)
    pending = admin.get("/api/admin/therapists?status=pending").get_json()
    assert pending["total"] == 1 and pending["items"][0]["credentials"][0]["details"] == "RCI-12345"
    assert admin.post(f"/api/admin/therapists/{tid}/verify", json={"approve": True}).status_code == 200
    assert len(public.get("/api/therapists").get_json()["therapists"]) == 1


def test_therapist_registration_validates_fields(client, h):
    r = client.post("/api/auth/register", json=h.therapist_payload(specializations=[], registration_number=""))
    assert r.status_code == 422 and "specializations" in r.get_json()["fields"]


def test_therapist_email_never_exposed_publicly(app, make_client, h):
    _, tid = h.approved_therapist(app, make_client)
    body = make_client().get(f"/api/therapists/{tid}").get_data(as_text=True)
    assert "doc@example.com" not in body and "email" not in body


def test_admin_endpoints_forbidden_for_non_admins(app, make_client, client, h):
    h.register(client); h.login(client)
    t, _ = h.approved_therapist(app, make_client)
    for c in (client, t):
        for path in ("/api/admin/analytics", "/api/admin/users", "/api/admin/therapists", "/api/admin/audit-logs"):
            assert c.get(path).status_code == 403, path


def test_user_cannot_use_therapist_portal(client, h):
    h.register(client); h.login(client)
    assert client.get("/api/therapist/overview").status_code == 403


# ---------- search / filters / matching ----------
def test_search_filters_and_matching(app, make_client, h):
    h.approved_therapist(app, make_client, "a@example.com", display_name="Dr. Anxiety", specializations=["anxiety"], languages=["te"], session_price=1000)
    h.approved_therapist(app, make_client, "b@example.com", display_name="Dr. Grief", specializations=["grief"], languages=["hi"], session_price=2500)
    c = make_client()
    assert len(c.get("/api/therapists?specialization=grief").get_json()["therapists"]) == 1
    assert len(c.get("/api/therapists?language=te").get_json()["therapists"]) == 1
    assert len(c.get("/api/therapists?max_price=1500").get_json()["therapists"]) == 1
    assert c.get("/api/therapists?q=anxiety").get_json()["therapists"][0]["display_name"] == "Dr. Anxiety"
    assert c.get("/api/therapists?specialization=trauma").get_json()["empty_message"]

    m = c.post("/api/matching", json={"concern": "anxiety", "language": "te", "budget": 1500, "mode": "audio", "time": "evening"}).get_json()
    top = m["matches"][0]
    assert top["therapist"]["display_name"] == "Dr. Anxiety" and top["score"] > m["matches"][1]["score"]
    assert any("anxiety" in r.lower() for r in top["reasons"])
    assert "not a clinical recommendation" in m["disclaimer"]


# ---------- booking ----------
def _client_user(make_client, h, email="client@example.com"):
    c = make_client(); h.register(c, email); h.login(c, email)
    return c


def test_booking_double_booking_and_rebooking_after_cancel(app, make_client, h):
    _, tid = h.approved_therapist(app, make_client)
    a, b = _client_user(make_client, h, "a@c.com"), _client_user(make_client, h, "b@c.com")
    slot = h.first_slot(a, tid)
    r1 = a.post("/api/appointments", json={"therapist_id": tid, "scheduled_start": slot, "session_mode": "video"})
    assert r1.status_code == 201
    r2 = b.post("/api/appointments", json={"therapist_id": tid, "scheduled_start": slot, "session_mode": "video"})
    assert r2.status_code == 409
    assert slot not in [s for d in a.get(f"/api/therapists/{tid}/slots?days=3").get_json()["days"] for s in d["slots"]]
    # cancelling frees the slot for someone else
    assert a.delete(f"/api/appointments/{r1.get_json()['appointment']['id']}").status_code == 200
    assert b.post("/api/appointments", json={"therapist_id": tid, "scheduled_start": slot, "session_mode": "audio"}).status_code == 201


def test_cannot_book_unoffered_time_or_mode_or_past(app, make_client, h):
    t, tid = h.approved_therapist(app, make_client, session_modes=["text"])
    c = _client_user(make_client, h)
    slot = h.first_slot(c, tid)
    assert c.post("/api/appointments", json={"therapist_id": tid, "scheduled_start": slot, "session_mode": "video"}).status_code == 422
    past = (utcnow() - timedelta(days=1)).isoformat() + "Z"
    assert c.post("/api/appointments", json={"therapist_id": tid, "scheduled_start": past, "session_mode": "text"}).status_code == 409
    odd = (utcnow() + timedelta(days=2, minutes=7)).isoformat() + "Z"
    assert c.post("/api/appointments", json={"therapist_id": tid, "scheduled_start": odd, "session_mode": "text"}).status_code == 409


def test_unpaid_hold_expires(app, make_client, h):
    _, tid = h.approved_therapist(app, make_client)
    a, b = _client_user(make_client, h, "a@c.com"), _client_user(make_client, h, "b@c.com")
    slot = h.first_slot(a, tid)
    appt = a.post("/api/appointments", json={"therapist_id": tid, "scheduled_start": slot, "session_mode": "video"}).get_json()["appointment"]
    with app.app_context():
        row = db.session.get(Appointment, appt["id"])
        row.created_at = utcnow() - timedelta(minutes=30)
        db.session.commit()
    assert b.post("/api/appointments", json={"therapist_id": tid, "scheduled_start": slot, "session_mode": "video"}).status_code == 201


def test_db_index_blocks_duplicate_active_slot(app, make_client, h):
    _, tid = h.approved_therapist(app, make_client)
    with app.app_context():
        u = User.query.filter_by(role="therapist").first()
        start = utcnow() + timedelta(days=3)
        mk = lambda status: Appointment(user_id=u.id, therapist_id=tid, scheduled_start=start, scheduled_end=start + timedelta(minutes=50), session_mode="text", status=status, price=1)
        db.session.add(mk("cancelled")); db.session.add(mk("confirmed")); db.session.commit()  # cancelled doesn't block
        db.session.add(mk("pending"))
        with pytest.raises(IntegrityError):
            db.session.commit()


# ---------- payment -> accept -> session -> chat ----------
def _paid_request(app, make_client, h, mode="text"):
    t, tid = h.approved_therapist(app, make_client)
    c = _client_user(make_client, h)
    slot = h.first_slot(c, tid)
    appt = c.post("/api/appointments", json={"therapist_id": tid, "scheduled_start": slot, "session_mode": mode}).get_json()["appointment"]
    order = c.post("/api/payments/create-order", json={"appointment_id": appt["id"]}).get_json()
    assert order["mode"] == "test"
    assert c.post("/api/payments/test-confirm", json={"payment_id": order["payment_id"]}).status_code == 200
    return t, c, appt["id"], tid


def test_payment_accept_and_session_flow(app, make_client, h):
    t, c, appt_id, _ = _paid_request(app, make_client, h)
    assert c.get(f"/api/appointments/{appt_id}").get_json()["appointment"]["status"] == "requested"
    assert c.get(f"/api/sessions/by-appointment/{appt_id}").status_code == 409  # not confirmed yet

    reqs = t.get("/api/therapist/appointments?status=requested").get_json()["appointments"]
    assert len(reqs) == 1 and "email" not in str(reqs[0]) and reqs[0]["client_name"].startswith("Anonymous User")
    assert t.post(f"/api/therapist/appointments/{appt_id}/respond", json={"action": "accept"}).status_code == 200

    sid = c.get(f"/api/sessions/by-appointment/{appt_id}").get_json()["session"]["id"]
    assert c.post(f"/api/messages/{sid}", json={"body": "hi"}).status_code == 409   # not live yet
    assert c.post(f"/api/sessions/{sid}/start").status_code == 200
    assert c.post(f"/api/messages/{sid}", json={"body": "Hello, doctor"}).status_code == 201
    msgs = t.get(f"/api/messages/{sid}").get_json()["messages"]
    assert [m["body"] for m in msgs] == ["Hello, doctor"] and msgs[0]["mine"] is False
    assert t.post(f"/api/messages/{sid}", json={"body": "Hi, how are you?"}).status_code == 201
    later = c.get(f"/api/messages/{sid}?after={msgs[0]['id']}").get_json()["messages"]
    assert [m["body"] for m in later] == ["Hi, how are you?"]

    assert t.post(f"/api/sessions/{sid}/end").status_code == 200
    assert c.get(f"/api/appointments/{appt_id}").get_json()["appointment"]["status"] == "completed"
    assert c.post(f"/api/messages/{sid}", json={"body": "late"}).status_code == 409
    assert c.post(f"/api/appointments/{appt_id}/review", json={"rating": 5, "comment": "Really helpful"}).status_code == 201
    assert c.post(f"/api/appointments/{appt_id}/review", json={"rating": 5}).status_code == 409
    earnings = t.get("/api/therapist/earnings").get_json()
    assert earnings["total_earned"] == 1200 and earnings["completed_sessions"] == 1


def test_session_and_chat_blocked_for_outsiders(app, make_client, h):
    t, c, appt_id, _ = _paid_request(app, make_client, h)
    t.post(f"/api/therapist/appointments/{appt_id}/respond", json={"action": "accept"})
    sid = c.get(f"/api/sessions/by-appointment/{appt_id}").get_json()["session"]["id"]
    c.post(f"/api/sessions/{sid}/start")
    outsider = _client_user(make_client, h, "eve@example.com")
    other_t, _ = h.approved_therapist(app, make_client, "other@example.com")
    for who in (outsider, other_t):
        assert who.get(f"/api/sessions/{sid}").status_code == 403
        assert who.get(f"/api/messages/{sid}").status_code == 403
        assert who.post(f"/api/messages/{sid}", json={"body": "x"}).status_code == 403
        assert who.post(f"/api/sessions/{sid}/end").status_code == 403
        assert who.get(f"/api/sessions/by-appointment/{appt_id}").status_code == 403


def test_decline_queues_refund(app, make_client, h):
    t, c, appt_id, _ = _paid_request(app, make_client, h)
    assert t.post(f"/api/therapist/appointments/{appt_id}/respond", json={"action": "decline"}).status_code == 200
    with app.app_context():
        assert Payment.query.first().status == "refund_pending"
        assert db.session.get(Appointment, appt_id).status == "declined"


def test_client_cancel_requested_gets_refund(app, make_client, h):
    _, c, appt_id, _ = _paid_request(app, make_client, h)
    r = c.delete(f"/api/appointments/{appt_id}")
    assert r.status_code == 200 and "refund" in r.get_json()["message"].lower()


def test_razorpay_signature_verification(app, make_client, h):
    _, tid = h.approved_therapist(app, make_client)
    c = _client_user(make_client, h)
    appt = c.post("/api/appointments", json={"therapist_id": tid, "scheduled_start": h.first_slot(c, tid), "session_mode": "text"}).get_json()["appointment"]
    with app.app_context():
        uid = User.query.filter_by(email="client@example.com").first().id
        p = Payment(user_id=uid, appointment_id=appt["id"], amount=120000, razorpay_order_id="order_ABC", mode="razorpay")
        db.session.add(p); db.session.commit()
    secret = app.config["RAZORPAY_KEY_SECRET"]
    bad = c.post("/api/payments/verify", json={"razorpay_order_id": "order_ABC", "razorpay_payment_id": "pay_1", "razorpay_signature": "0" * 64})
    assert bad.status_code == 400
    with app.app_context():
        assert db.session.get(Appointment, appt["id"]).status == "pending"
    good = c.post("/api/payments/verify", json={"razorpay_order_id": "order_ABC", "razorpay_payment_id": "pay_1", "razorpay_signature": h.sign("order_ABC", "pay_1", secret)})
    assert good.status_code == 200   # a genuine retry on the same order still succeeds
    assert c.get(f"/api/appointments/{appt['id']}").get_json()["appointment"]["status"] == "requested"


def test_razorpay_valid_signature_marks_paid(app, make_client, h):
    _, tid = h.approved_therapist(app, make_client)
    c = _client_user(make_client, h)
    appt = c.post("/api/appointments", json={"therapist_id": tid, "scheduled_start": h.first_slot(c, tid), "session_mode": "text"}).get_json()["appointment"]
    with app.app_context():
        uid = User.query.filter_by(email="client@example.com").first().id
        db.session.add(Payment(user_id=uid, appointment_id=appt["id"], amount=120000, razorpay_order_id="order_XYZ", mode="razorpay"))
        db.session.commit()
    sig = h.sign("order_XYZ", "pay_9", app.config["RAZORPAY_KEY_SECRET"])
    assert c.post("/api/payments/verify", json={"razorpay_order_id": "order_XYZ", "razorpay_payment_id": "pay_9", "razorpay_signature": sig}).status_code == 200
    assert c.get(f"/api/appointments/{appt['id']}").get_json()["appointment"]["status"] == "requested"


def test_user_cannot_touch_someone_elses_appointment(app, make_client, h):
    _, c, appt_id, _ = _paid_request(app, make_client, h)
    other = _client_user(make_client, h, "other@c.com")
    assert other.get(f"/api/appointments/{appt_id}").status_code == 404
    assert other.delete(f"/api/appointments/{appt_id}").status_code == 404
    assert other.post("/api/payments/create-order", json={"appointment_id": appt_id}).status_code == 404


# ---------- privacy ----------
def test_journal_is_private_and_deleted_with_account(app, make_client, h):
    a, b = _client_user(make_client, h, "a@c.com"), _client_user(make_client, h, "b@c.com")
    entry = a.post("/api/journal", json={"body": "very private", "mood_tag": "low"}).get_json()["entry"]
    assert b.get("/api/journal").get_json()["entries"] == []
    assert b.put(f"/api/journal/{entry['id']}", json={"body": "hacked"}).status_code == 404
    assert b.delete(f"/api/journal/{entry['id']}").status_code == 404
    t, _ = h.approved_therapist(app, make_client)
    assert t.get("/api/journal").get_json()["entries"] == []
    assert a.delete("/api/users/me", json={"password": "wrong"}).status_code == 403
    assert a.delete("/api/users/me", json={"password": "StrongPass123"}).status_code == 200
    with app.app_context():
        assert JournalEntry.query.count() == 0
        assert User.query.filter_by(email="a@c.com").first() is None
    assert h.login(make_client(), "a@c.com").status_code == 401


def test_pre_session_summary_only_visible_when_shared(app, make_client, h):
    t, c, appt_id, _ = _paid_request(app, make_client, h)
    c.post("/api/check-in", json={"text": "I feel anxious and on edge about work"})
    assert t.get(f"/api/therapist/appointments/{appt_id}/pre-session").get_json()["shared"] is False
    c.put(f"/api/appointments/{appt_id}", json={"action": "share_summary", "share": True})
    got = t.get(f"/api/therapist/appointments/{appt_id}/pre-session").get_json()
    assert got["shared"] is True and got["summary"]["primary_emotion"] == "anxiety" and "score" not in str(got)


# ---------- AI ----------
def test_check_in_is_supportive_and_hides_raw_score(client, h):
    h.register(client); h.login(client)
    r = client.post("/api/check-in", json={"text": "I can't cope, I feel hopeless and I want to die"}).get_json()
    assert r["risk"]["tier"] == "high" and r["show_safety_resources"] and r["emergency_note"]
    assert "score" not in r["risk"] and "not a medical diagnosis" in r["risk"]["disclaimer"]
    assert "you have" not in r["message"].lower()
    assert len(client.get("/api/check-in/history").get_json()["history"]) == 1


def test_risk_service_tiers():
    from app.ai.risk_service import assess_risk
    assert assess_risk("I had a lovely day", {})["tier"] == "low"
    assert assess_risk("I feel hopeless", {})["tier"] == "moderate"
    assert assess_risk("I want to kill myself", {})["tier"] == "high"


# ---------- wellness ----------
def test_recovery_progress_is_sequential_and_streaks(client, h):
    h.register(client); h.login(client)
    assert client.post("/api/recovery/complete", json={"day": 3}).status_code == 409
    assert client.post("/api/recovery/complete", json={"day": 1}).status_code == 200
    r = client.post("/api/recovery/complete", json={"day": 2}).get_json()
    assert r["streak"] == 2
    client.post("/api/journal", json={"body": "ok day", "mood_tag": "good"})
    p = client.get("/api/progress").get_json()
    assert p["totals"]["recovery_streak"] == 2 and p["mood_trend"][0]["score"] == 4


def test_safety_plan_private_per_user(make_client, h):
    a, b = _client_user(make_client, h, "a@c.com"), _client_user(make_client, h, "b@c.com")
    a.put("/api/safety-plan", json={"safe_locations": ["Sister's home"], "trusted_contacts": [{"name": "Asha", "phone": "123"}]})
    assert a.get("/api/safety-plan").get_json()["safety_plan"]["trusted_contacts"][0]["name"] == "Asha"
    assert b.get("/api/safety-plan").get_json()["safety_plan"] is None


# ---------- admin ----------
def test_admin_suspension_blocks_existing_sessions_and_is_audited(app, make_client, h):
    victim = _client_user(make_client, h, "v@c.com")
    admin = make_client(); h.make_admin(app, admin)
    uid = victim.get("/api/auth/me").get_json()["user"]["id"]
    assert admin.post(f"/api/admin/users/{uid}/suspend").status_code == 200
    assert victim.get("/api/auth/me").status_code == 401                       # existing cookie no longer works
    assert h.login(make_client(), "v@c.com").status_code == 403
    assert admin.post(f"/api/admin/users/{uid}/activate").status_code == 200
    assert h.login(make_client(), "v@c.com").status_code == 200
    actions = [l["action"] for l in admin.get("/api/admin/audit-logs").get_json()["items"]]
    assert "user_suspended" in actions and "user_reactivated" in actions


def test_admin_cannot_suspend_admin_and_analytics_shape(app, make_client, h):
    admin = make_client(); h.make_admin(app, admin)
    aid = admin.get("/api/auth/me").get_json()["user"]["id"]
    assert admin.post(f"/api/admin/users/{aid}/suspend").status_code == 403
    a = admin.get("/api/admin/analytics").get_json()
    assert {"totals", "series", "session_types", "top_therapists"} <= set(a)
    assert len(a["series"]["signups"]) == 14
    assert admin.get("/api/admin/system").get_json()["database"] == "ok"


def test_admin_resources_crud_and_public_visibility(app, make_client, h):
    admin = make_client(); h.make_admin(app, admin)
    r = admin.post("/api/admin/resources", json={"title": "Grounding", "body": "5-4-3-2-1", "category": "anxiety"})
    assert r.status_code == 201
    rid = r.get_json()["resource"]["id"]
    public = make_client()
    assert len(public.get("/api/resources").get_json()["resources"]) == 1
    admin.put(f"/api/admin/resources/{rid}", json={"title": "Grounding", "body": "x", "category": "anxiety", "is_published": False})
    assert public.get("/api/resources").get_json()["resources"] == []
    assert admin.delete(f"/api/admin/resources/{rid}").status_code == 200
    assert admin.post("/api/admin/resources", json={"title": "", "body": "", "category": "nope"}).status_code == 422


def test_admin_never_sees_private_content(app, make_client, h):
    _, c, appt_id, _ = _paid_request(app, make_client, h)
    c.post("/api/journal", json={"body": "SECRET-JOURNAL-TEXT"})
    c.post("/api/check-in", json={"text": "SECRET-CHECKIN-TEXT anxious"})
    admin = make_client(); h.make_admin(app, admin)
    blob = "".join(admin.get(p).get_data(as_text=True) for p in (
        "/api/admin/analytics", "/api/admin/users", "/api/admin/appointments", "/api/admin/payments", "/api/admin/audit-logs"))
    assert "SECRET-JOURNAL-TEXT" not in blob and "SECRET-CHECKIN-TEXT" not in blob


def test_suspended_therapist_disappears_from_public_list(app, make_client, h):
    t, tid = h.approved_therapist(app, make_client)
    admin = make_client(); h.make_admin(app, admin, "boss@example.com")
    uid = t.get("/api/auth/me").get_json()["user"]["id"]
    admin.post(f"/api/admin/users/{uid}/suspend")
    assert make_client().get("/api/therapists").get_json()["therapists"] == []
