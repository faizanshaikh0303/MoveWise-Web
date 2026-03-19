"""Integration tests for /profile endpoints."""
import pytest

FULL_PROFILE = {
    "work_hours": "9:00 - 17:00",
    "work_address": "789 Work St, New York, NY",
    "commute_preference": "driving",
    "sleep_hours": "23:00 - 07:00",
    "noise_preference": "moderate",
    "hobbies": ["gym", "hiking"],
}


class TestCreateOrUpdateProfile:
    def test_create_full_profile(self, client, test_user, auth_headers):
        resp = client.post("/profile/", json=FULL_PROFILE, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["work_hours"] == "9:00 - 17:00"
        assert data["noise_preference"] == "moderate"
        assert data["hobbies"] == ["gym", "hiking"]
        assert data["user_id"] == test_user.id
        assert "id" in data

    def test_create_empty_profile(self, client, test_user, auth_headers):
        resp = client.post("/profile/", json={}, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["work_hours"] is None
        assert data["hobbies"] is None

    def test_upsert_updates_existing_profile(self, client, test_user, auth_headers, user_profile):
        resp = client.post("/profile/", json={
            **FULL_PROFILE,
            "noise_preference": "quiet",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["noise_preference"] == "quiet"

    def test_upsert_does_not_create_duplicate(self, client, test_user, auth_headers, user_profile):
        original_id = user_profile.id
        client.post("/profile/", json=FULL_PROFILE, headers=auth_headers)
        get_resp = client.get("/profile/", headers=auth_headers)
        assert get_resp.json()["id"] == original_id

    def test_hobbies_empty_list(self, client, test_user, auth_headers):
        resp = client.post("/profile/", json={**FULL_PROFILE, "hobbies": []}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["hobbies"] == []

    def test_no_auth_returns_403(self, client):
        resp = client.post("/profile/", json=FULL_PROFILE)
        assert resp.status_code == 403

    def test_response_contains_timestamps(self, client, test_user, auth_headers):
        resp = client.post("/profile/", json=FULL_PROFILE, headers=auth_headers)
        data = resp.json()
        assert "created_at" in data
        assert "updated_at" in data


class TestGetProfile:
    def test_returns_existing_profile(self, client, test_user, auth_headers, user_profile):
        resp = client.get("/profile/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["work_hours"] == "9:00 - 17:00"
        assert data["hobbies"] == ["gym", "hiking"]

    def test_returns_null_when_no_profile(self, client, test_user, auth_headers):
        resp = client.get("/profile/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() is None

    def test_no_auth_returns_403(self, client):
        resp = client.get("/profile/")
        assert resp.status_code == 403

    def test_does_not_return_other_users_profile(self, client, db, test_user, auth_headers):
        from app.models.user import User
        from app.core.security import get_password_hash
        from app.models.profile import UserProfile

        other = User(email="other@example.com", hashed_password=get_password_hash("pw"))
        db.add(other)
        db.commit()
        db.refresh(other)

        other_profile = UserProfile(user_id=other.id, noise_preference="quiet")
        db.add(other_profile)
        db.commit()

        # test_user has no profile
        resp = client.get("/profile/", headers=auth_headers)
        assert resp.json() is None


class TestUpdateProfile:
    def test_update_single_field(self, client, test_user, auth_headers, user_profile):
        resp = client.put("/profile/", json={"noise_preference": "quiet"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["noise_preference"] == "quiet"

    def test_update_preserves_other_fields(self, client, test_user, auth_headers, user_profile):
        resp = client.put("/profile/", json={"hobbies": ["cooking"]}, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["hobbies"] == ["cooking"]
        assert data["work_hours"] == "9:00 - 17:00"  # unchanged

    def test_update_nonexistent_profile_returns_404(self, client, test_user, auth_headers):
        resp = client.put("/profile/", json={"noise_preference": "quiet"}, headers=auth_headers)
        assert resp.status_code == 404

    def test_update_with_empty_body(self, client, test_user, auth_headers, user_profile):
        resp = client.put("/profile/", json={}, headers=auth_headers)
        assert resp.status_code == 200
        # Nothing should change
        assert resp.json()["work_hours"] == "9:00 - 17:00"

    def test_no_auth_returns_403(self, client):
        resp = client.put("/profile/", json={"noise_preference": "quiet"})
        assert resp.status_code == 403
