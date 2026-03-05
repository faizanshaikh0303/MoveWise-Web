"""
Tests for /auth/* endpoints:
  POST /auth/register
  POST /auth/login
  GET  /auth/me
  PUT  /auth/change-password
"""


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegister:
    def test_register_new_user_returns_token(self, client):
        resp = client.post("/auth/register", json={
            "email": "new@example.com",
            "name": "Alice",
            "password": "secret123",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert len(body["access_token"]) > 20

    def test_register_without_name_succeeds(self, client):
        resp = client.post("/auth/register", json={
            "email": "noname@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_register_duplicate_email_returns_400(self, client):
        payload = {"email": "dup@example.com", "password": "abc123"}
        client.post("/auth/register", json=payload)
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"].lower()

    def test_register_invalid_email_returns_422(self, client):
        resp = client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "abc123",
        })
        assert resp.status_code == 422

    def test_register_missing_password_returns_422(self, client):
        resp = client.post("/auth/register", json={"email": "a@b.com"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_valid_credentials_returns_token(self, client, registered_user):
        resp = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password_returns_401(self, client, registered_user):
        resp = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": "wrong-password",
        })
        assert resp.status_code == 401
        assert "incorrect" in resp.json()["detail"].lower()

    def test_login_nonexistent_user_returns_401(self, client):
        resp = client.post("/auth/login", json={
            "email": "ghost@example.com",
            "password": "doesntmatter",
        })
        assert resp.status_code == 401

    def test_login_invalid_email_format_returns_422(self, client):
        resp = client.post("/auth/login", json={
            "email": "bad-email",
            "password": "password",
        })
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------

class TestGetCurrentUser:
    def test_me_with_valid_token_returns_user(self, client, registered_user):
        resp = client.get("/auth/me", headers=registered_user["headers"])
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == registered_user["email"]
        assert body["name"] == registered_user["name"]
        assert "id" in body
        assert "created_at" in body
        assert "profile_setup_complete" in body

    def test_me_profile_setup_complete_false_before_profile(self, client, registered_user):
        resp = client.get("/auth/me", headers=registered_user["headers"])
        assert resp.json()["profile_setup_complete"] is False

    def test_me_profile_setup_complete_true_after_profile(self, client, registered_user):
        client.post("/profile/", json={
            "work_hours": "9:00 - 17:00",
            "noise_preference": "moderate",
        }, headers=registered_user["headers"])
        resp = client.get("/auth/me", headers=registered_user["headers"])
        assert resp.json()["profile_setup_complete"] is True

    def test_me_without_token_returns_403(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 403

    def test_me_with_invalid_token_returns_401(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert resp.status_code == 401

    def test_me_with_malformed_header_returns_403(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "NotBearer xyz"})
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PUT /auth/change-password
# ---------------------------------------------------------------------------

class TestChangePassword:
    def test_change_password_success(self, client, registered_user):
        resp = client.put("/auth/change-password", json={
            "current_password": registered_user["password"],
            "new_password": "newpassword456",
        }, headers=registered_user["headers"])
        assert resp.status_code == 200
        assert "success" in resp.json()["message"].lower()

    def test_can_login_with_new_password_after_change(self, client, registered_user):
        client.put("/auth/change-password", json={
            "current_password": registered_user["password"],
            "new_password": "newpassword456",
        }, headers=registered_user["headers"])

        login_resp = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": "newpassword456",
        })
        assert login_resp.status_code == 200

    def test_old_password_rejected_after_change(self, client, registered_user):
        client.put("/auth/change-password", json={
            "current_password": registered_user["password"],
            "new_password": "newpassword456",
        }, headers=registered_user["headers"])

        login_resp = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        assert login_resp.status_code == 401

    def test_change_password_wrong_current_returns_400(self, client, registered_user):
        resp = client.put("/auth/change-password", json={
            "current_password": "thisiswrong",
            "new_password": "newpassword456",
        }, headers=registered_user["headers"])
        assert resp.status_code == 400
        assert "incorrect" in resp.json()["detail"].lower()

    def test_change_password_requires_auth(self, client):
        resp = client.put("/auth/change-password", json={
            "current_password": "old",
            "new_password": "new",
        })
        assert resp.status_code == 403
