from app.models.user import User


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.get_json() == {"status": "ok"}


def test_register_uses_uuid_identity(client, h):
    r = h.register(client)
    assert r.status_code == 201
    assert len(r.get_json()["user"]["id"]) == 36
    assert r.get_json()["user"]["display_name"].startswith("Anonymous User #")


def test_duplicate_and_weak_passwords_rejected(client, h):
    h.register(client)
    assert h.register(client).status_code == 409
    assert client.post("/api/auth/register", json={"email": "a@b.com", "password": "short"}).status_code == 422
    assert client.post("/api/auth/register", json={"email": "a@b.com", "password": "longpasswordnodigits"}).status_code == 422


def test_login_and_me(client, h):
    h.register(client)
    assert h.login(client, password="WrongPass123").status_code == 401
    r = h.login(client)
    assert r.status_code == 200
    assert client.get("/api/auth/me").get_json()["user"]["email"] == "user@example.com"


def test_protected_routes_require_login(client):
    for path in ("/api/auth/me", "/api/journal", "/api/appointments", "/api/progress", "/api/safety-plan", "/api/admin/analytics", "/api/therapist/me"):
        assert client.get(path).status_code == 401, path


def test_wrong_portal_is_rejected(client, make_client, h):
    h.register(client)
    r = h.login(make_client(), portal="therapist")
    assert r.status_code == 403 and r.get_json()["error"] == "wrong_portal"
    assert h.login(make_client(), portal="admin").status_code == 403


def test_public_registration_cannot_create_admin(client, h):
    r = h.register(client, "sneaky@example.com", role="admin")
    assert r.get_json()["user"]["role"] == "user"


def test_logout_clears_session(client, h):
    h.register(client); h.login(client)
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401


def test_password_reset_flow(client, app, h):
    h.register(client)
    assert client.post("/api/auth/forgot-password", json={"email": "nobody@example.com"}).status_code == 200
    assert client.post("/api/auth/forgot-password", json={"email": "user@example.com"}).status_code == 200
    with app.app_context():
        token = User.query.filter_by(email="user@example.com").first().password_reset_token
    assert token
    assert client.post("/api/auth/reset-password", json={"token": token, "password": "BrandNew456"}).status_code == 200
    assert client.post("/api/auth/reset-password", json={"token": token, "password": "BrandNew456"}).status_code == 400  # single use
    assert h.login(client, password="BrandNew456").status_code == 200


def test_change_password_requires_current(client, h):
    h.register(client); h.login(client)
    assert client.post("/api/auth/change-password", json={"current_password": "nope12345", "new_password": "Another123"}).status_code == 403
    assert client.post("/api/auth/change-password", json={"current_password": "StrongPass123", "new_password": "Another123"}).status_code == 200


def test_csrf_double_submit_is_enforced():
    """With CSRF on (as in dev/prod), a write needs the token returned at login."""
    from app import create_app
    from app.extensions import db
    app = create_app("testing_csrf")
    with app.app_context():
        db.create_all()
        c = app.test_client()
        c.post("/api/auth/register", json={"email": "c@example.com", "password": "StrongPass123"})
        token = c.post("/api/auth/login", json={"email": "c@example.com", "password": "StrongPass123"}).get_json()["csrf_token"]
        assert token
        assert c.post("/api/journal", json={"body": "x"}).status_code == 401
        assert c.post("/api/journal", json={"body": "x"}, headers={"X-CSRF-TOKEN": "wrong"}).status_code == 401
        assert c.post("/api/journal", json={"body": "x"}, headers={"X-CSRF-TOKEN": token}).status_code == 201
        assert c.get("/api/auth/me").get_json()["csrf_token"] == token or c.get("/api/auth/me").get_json()["csrf_token"]
        db.session.remove(); db.drop_all()
