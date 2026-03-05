"""
Tests for /profile/* endpoints:
  POST /profile/   – create or update
  GET  /profile/   – read
  PUT  /profile/   – update (requires existing profile)
"""


FULL_PROFILE = {
    "work_hours": "9:00 AM - 5:00 PM",
    "work_address": "123 Office St, New York, NY",
    "commute_preference": "driving",
    "sleep_hours": "11:00 PM - 7:00 AM",
    "noise_preference": "quiet",
    "hobbies": ["gym", "hiking", "restaurants"],
}


# ---------------------------------------------------------------------------
# POST /profile/
# ---------------------------------------------------------------------------

class TestCreateProfile:
    def test_create_profile_returns_profile_data(self, client, auth_headers):
        resp = client.post("/profile/", json=FULL_PROFILE, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["work_hours"] == FULL_PROFILE["work_hours"]
        assert body["work_address"] == FULL_PROFILE["work_address"]
        assert body["commute_preference"] == FULL_PROFILE["commute_preference"]
        assert body["noise_preference"] == FULL_PROFILE["noise_preference"]
        assert body["hobbies"] == FULL_PROFILE["hobbies"]
        assert "id" in body
        assert "user_id" in body
        assert "created_at" in body

    def test_create_profile_with_minimal_data(self, client, auth_headers):
        resp = client.post("/profile/", json={}, headers=auth_headers)
        assert resp.status_code == 200

    def test_create_profile_twice_updates_existing(self, client, auth_headers):
        client.post("/profile/", json={"noise_preference": "quiet"}, headers=auth_headers)
        resp = client.post("/profile/", json={"noise_preference": "loud"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["noise_preference"] == "loud"

        # Still only one profile in the DB
        get_resp = client.get("/profile/", headers=auth_headers)
        assert get_resp.json()["noise_preference"] == "loud"

    def test_create_profile_requires_auth(self, client):
        resp = client.post("/profile/", json=FULL_PROFILE)
        assert resp.status_code == 403

    def test_hobbies_stored_as_list(self, client, auth_headers):
        resp = client.post("/profile/", json={"hobbies": ["gym", "hiking"]}, headers=auth_headers)
        assert isinstance(resp.json()["hobbies"], list)
        assert "gym" in resp.json()["hobbies"]


# ---------------------------------------------------------------------------
# GET /profile/
# ---------------------------------------------------------------------------

class TestGetProfile:
    def test_get_profile_returns_null_when_none_exists(self, client, auth_headers):
        resp = client.get("/profile/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() is None

    def test_get_profile_returns_profile_after_creation(self, client, auth_headers):
        client.post("/profile/", json=FULL_PROFILE, headers=auth_headers)
        resp = client.get("/profile/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["work_hours"] == FULL_PROFILE["work_hours"]

    def test_get_profile_requires_auth(self, client):
        resp = client.get("/profile/")
        assert resp.status_code == 403

    def test_profile_belongs_to_correct_user(self, client, auth_headers, second_user):
        """User A's profile should not be visible to User B."""
        client.post("/profile/", json={"noise_preference": "quiet"}, headers=auth_headers)
        resp = client.get("/profile/", headers=second_user["headers"])
        assert resp.json() is None


# ---------------------------------------------------------------------------
# PUT /profile/
# ---------------------------------------------------------------------------

class TestUpdateProfile:
    def test_update_existing_profile(self, client, auth_headers):
        client.post("/profile/", json=FULL_PROFILE, headers=auth_headers)
        resp = client.put("/profile/", json={"noise_preference": "moderate"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["noise_preference"] == "moderate"

    def test_update_preserves_unset_fields(self, client, auth_headers):
        client.post("/profile/", json=FULL_PROFILE, headers=auth_headers)
        client.put("/profile/", json={"noise_preference": "moderate"}, headers=auth_headers)
        get_resp = client.get("/profile/", headers=auth_headers)
        # work_hours should still be set from the original POST
        assert get_resp.json()["work_hours"] == FULL_PROFILE["work_hours"]

    def test_update_hobbies_list(self, client, auth_headers):
        client.post("/profile/", json={"hobbies": ["gym"]}, headers=auth_headers)
        resp = client.put("/profile/", json={"hobbies": ["hiking", "restaurants"]}, headers=auth_headers)
        assert resp.json()["hobbies"] == ["hiking", "restaurants"]

    def test_update_profile_when_none_returns_404(self, client, auth_headers):
        resp = client.put("/profile/", json={"noise_preference": "moderate"}, headers=auth_headers)
        assert resp.status_code == 404

    def test_update_profile_requires_auth(self, client):
        resp = client.put("/profile/", json={"noise_preference": "quiet"})
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# profile_setup_complete behaviour via /auth/me
# ---------------------------------------------------------------------------

class TestProfileSetupComplete:
    def test_flag_false_before_profile(self, client, auth_headers):
        resp = client.get("/auth/me", headers=auth_headers)
        assert resp.json()["profile_setup_complete"] is False

    def test_flag_true_after_profile_created(self, client, auth_headers):
        client.post("/profile/", json={}, headers=auth_headers)
        resp = client.get("/auth/me", headers=auth_headers)
        assert resp.json()["profile_setup_complete"] is True
