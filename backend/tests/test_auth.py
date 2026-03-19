"""Integration tests for /auth endpoints."""
import pytest


class TestRegister:
    def test_success_returns_token(self, client):
        resp = client.post("/auth/register", json={
            "email": "new@example.com",
            "password": "password123",
            "name": "New User",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_success_without_name(self, client):
        resp = client.post("/auth/register", json={
            "email": "noname@example.com",
            "password": "password123",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_duplicate_email_returns_400(self, client, test_user):
        resp = client.post("/auth/register", json={
            "email": "test@example.com",  # already exists
            "password": "different123",
        })
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"].lower()

    def test_invalid_email_format_returns_422(self, client):
        resp = client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "password123",
        })
        assert resp.status_code == 422

    def test_missing_email_returns_422(self, client):
        resp = client.post("/auth/register", json={"password": "password123"})
        assert resp.status_code == 422

    def test_missing_password_returns_422(self, client):
        resp = client.post("/auth/register", json={"email": "a@example.com"})
        assert resp.status_code == 422

    def test_registered_user_can_login(self, client):
        client.post("/auth/register", json={
            "email": "fresh@example.com",
            "password": "mypassword",
        })
        login = client.post("/auth/login", json={
            "email": "fresh@example.com",
            "password": "mypassword",
        })
        assert login.status_code == 200


class TestLogin:
    def test_success_returns_token(self, client, test_user):
        resp = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "password123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_wrong_password_returns_401(self, client, test_user):
        resp = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_nonexistent_user_returns_401(self, client):
        resp = client.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": "password123",
        })
        assert resp.status_code == 401

    def test_invalid_email_format_returns_422(self, client):
        resp = client.post("/auth/login", json={
            "email": "not-an-email",
            "password": "password123",
        })
        assert resp.status_code == 422

    def test_empty_password_returns_401(self, client, test_user):
        resp = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "",
        })
        assert resp.status_code == 401

    def test_missing_password_field_returns_422(self, client):
        resp = client.post("/auth/login", json={"email": "test@example.com"})
        assert resp.status_code == 422


class TestGetCurrentUser:
    def test_returns_user_data(self, client, test_user, auth_headers):
        resp = client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert data["id"] == test_user.id
        assert "profile_setup_complete" in data

    def test_hashed_password_not_exposed(self, client, test_user, auth_headers):
        resp = client.get("/auth/me", headers=auth_headers)
        assert "hashed_password" not in resp.json()
        assert "password" not in resp.json()

    def test_no_token_returns_403(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 403

    def test_invalid_token_returns_401(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
        assert resp.status_code == 401

    def test_malformed_auth_header_returns_403(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "Token sometoken"})
        assert resp.status_code == 403

    def test_profile_setup_complete_false_without_profile(self, client, test_user, auth_headers):
        resp = client.get("/auth/me", headers=auth_headers)
        assert resp.json()["profile_setup_complete"] is False

    def test_profile_setup_complete_true_after_profile_created(self, client, test_user, auth_headers):
        client.post("/profile/", json={"noise_preference": "quiet"}, headers=auth_headers)
        resp = client.get("/auth/me", headers=auth_headers)
        assert resp.json()["profile_setup_complete"] is True

    def test_expired_token_returns_401(self, client, test_user):
        from datetime import timedelta
        from app.core.security import create_access_token
        expired = create_access_token(
            data={"sub": test_user.email},
            expires_delta=timedelta(seconds=-1),
        )
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})
        assert resp.status_code == 401

    def test_token_for_deleted_user_returns_401(self, client, db):
        from app.core.security import get_password_hash, create_access_token
        from app.models.user import User
        ghost = User(email="ghost@example.com", hashed_password=get_password_hash("pw"))
        db.add(ghost)
        db.commit()
        token = create_access_token(data={"sub": ghost.email})
        db.delete(ghost)
        db.commit()
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401


class TestChangePassword:
    def test_success(self, client, test_user, auth_headers):
        resp = client.put("/auth/change-password", json={
            "current_password": "password123",
            "new_password": "newpassword456",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["message"] == "Password changed successfully"

    def test_wrong_current_password_returns_400(self, client, test_user, auth_headers):
        resp = client.put("/auth/change-password", json={
            "current_password": "wrongpassword",
            "new_password": "newpassword456",
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_new_password_too_short_returns_422(self, client, test_user, auth_headers):
        resp = client.put("/auth/change-password", json={
            "current_password": "password123",
            "new_password": "abc",  # less than 6 chars
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_exactly_6_chars_accepted(self, client, test_user, auth_headers):
        resp = client.put("/auth/change-password", json={
            "current_password": "password123",
            "new_password": "abc123",
        }, headers=auth_headers)
        assert resp.status_code == 200

    def test_old_password_rejected_after_change(self, client, test_user, auth_headers):
        client.put("/auth/change-password", json={
            "current_password": "password123",
            "new_password": "newpassword456",
        }, headers=auth_headers)
        resp = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "password123",
        })
        assert resp.status_code == 401

    def test_new_password_works_after_change(self, client, test_user, auth_headers):
        client.put("/auth/change-password", json={
            "current_password": "password123",
            "new_password": "newpassword456",
        }, headers=auth_headers)
        resp = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "newpassword456",
        })
        assert resp.status_code == 200

    def test_no_auth_returns_403(self, client):
        resp = client.put("/auth/change-password", json={
            "current_password": "password123",
            "new_password": "newpassword456",
        })
        assert resp.status_code == 403
