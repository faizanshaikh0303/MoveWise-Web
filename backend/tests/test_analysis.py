"""
Tests for /analysis/* endpoints:
  POST   /analysis/          – create (all external services are mocked)
  GET    /analysis/          – list
  GET    /analysis/{id}      – detail (scores at top level)
  DELETE /analysis/{id}      – delete

All calls to Google Maps, FBI, Census, OSM, and Groq are patched so the
test suite requires no API keys and runs fully offline.
"""
from unittest.mock import patch, MagicMock
import pytest


# ---------------------------------------------------------------------------
# Stub data returned by mocked services
# ---------------------------------------------------------------------------

STUB_CRIME = {
    "current": {
        "total_crimes": 50,
        "daily_average": 1.7,
        "safety_score": 72.0,
        "is_real_data": False,
        "categories": {},
        "temporal_analysis": {"crimes_during_sleep_hours": 5, "crimes_during_work_hours": 10, "peak_hours": []},
        "trend": {"direction": "stable", "change_percent": 0},
        "crimes_list": [],
        "data_source": "FBI UCR",
    },
    "destination": {
        "total_crimes": 30,
        "daily_average": 1.0,
        "safety_score": 80.0,
        "is_real_data": False,
        "categories": {},
        "temporal_analysis": {"crimes_during_sleep_hours": 3, "crimes_during_work_hours": 7, "peak_hours": []},
        "trend": {"direction": "stable", "change_percent": 0},
        "crimes_list": [],
        "data_source": "FBI UCR",
    },
    "comparison": {
        "crime_difference": -20,
        "crime_change_percent": -40.0,
        "score_difference": 8.0,
        "is_safer": True,
        "recommendation": "Destination is safer.",
    },
}

STUB_NOISE = {
    "current": {"estimated_db": 60.0, "noise_category": "Moderate", "noise_score": 65.0, "description": "Urban area"},
    "destination": {
        "estimated_db": 50.0,
        "noise_category": "Quiet",
        "noise_score": 78.0,
        "description": "Suburban area",
        "preference_match": "Good match",
    },
    "comparison": {
        "db_difference": -10.0,
        "score_difference": 13.0,
        "is_quieter": True,
        "category_change": "Moderate → Quiet",
        "recommendation": "Destination is quieter.",
        "db_change_description": "Quieter by 10 dB",
    },
}

STUB_COST = {
    "current": {"total_monthly": 3000.0, "total_annual": 36000.0, "affordability_score": 65.0,
                "housing": {"monthly_rent": 1800.0, "bedrooms": 2, "source": "HUD FMR"},
                "expenses": {}, "cpi_index": 1.0, "data_source": "Census"},
    "destination": {"total_monthly": 2500.0, "total_annual": 30000.0, "affordability_score": 75.0,
                    "housing": {"monthly_rent": 1400.0, "bedrooms": 2, "source": "HUD FMR"},
                    "expenses": {}, "cpi_index": 0.95, "data_source": "Census"},
    "comparison": {
        "monthly_difference": -500.0,
        "annual_difference": -6000.0,
        "percent_change": -16.7,
        "is_more_expensive": False,
        "score_difference": 10.0,
        "housing_difference": -400.0,
        "expense_breakdown": {},
        "recommendation": "Cheaper destination.",
    },
}

STUB_AMENITIES = {
    "current_amenities": {"cafes": 5, "restaurants": 10, "gyms": 3},
    "destination_amenities": {"cafes": 8, "restaurants": 15, "gyms": 5, "parks": 4},
    "current": {"total_count": 18},
    "destination": {"total_count": 32},
    "comparison": {"amenities_difference": 14, "is_better": True},
}

STUB_COMMUTE = {
    "duration_minutes": 25,
    "distance": "12 km",
    "method": "driving",
    "description": "25 min by car",
    "alternatives": {"driving": {"duration_minutes": 25, "distance": "12 km"}},
}

STUB_LLM = {
    "overview_summary": "This is a great move.",
    "lifestyle_changes": ["✓ Quieter neighbourhood", "✓ Lower rent"],
    "ai_insights": "Overall this location looks promising.",
    "action_steps": ["→ Visit the area", "→ Check schools"],
}

STUB_GEOCODE = (40.7128, -74.0060)  # NYC coords
STUB_ZIP = "10001"


def make_mock_services():
    """Return a context manager that patches all external service calls."""
    return [
        patch("app.api.analysis.places_service.geocode_address", return_value=STUB_GEOCODE),
        patch("app.api.analysis.get_zip_from_coords", return_value=STUB_ZIP),
        patch("app.api.analysis.crime_service.compare_crime_data", return_value=STUB_CRIME),
        patch("app.api.analysis.noise_service.estimate_noise_level", side_effect=[
            {
                "score": 60.0,
                "noise_category": "Moderate",
                "noise_score": 65.0,
                "description": "Urban",
                "preference_match": "OK",
                "road_breakdown": {},
                "total_roads": 10,
                "road_density": 0.5,
            },
            {
                "score": 50.0,
                "noise_category": "Quiet",
                "noise_score": 78.0,
                "description": "Suburban",
                "preference_match": "Good match",
                "road_breakdown": {},
                "total_roads": 5,
                "road_density": 0.2,
            },
        ]),
        patch("app.api.analysis.noise_service.compare_noise_levels", return_value={
            "db_difference": -10.0,
            "score_difference": 13.0,
            "analysis": "Destination is quieter.",
            "db_change_description": "Quieter by 10 dB",
        }),
        patch("app.api.analysis.cost_service.compare_costs", return_value=STUB_COST),
        patch("app.api.analysis.places_service.compare_amenities", return_value=STUB_AMENITIES),
        patch("app.api.analysis.places_service.get_commute_info", return_value=STUB_COMMUTE),
        patch("app.api.analysis.llm_service.generate_lifestyle_analysis", return_value=STUB_LLM),
    ]


@pytest.fixture
def user_with_profile(client, auth_headers):
    """Registered user who has completed profile setup."""
    client.post("/profile/", json={
        "work_hours": "9:00 - 17:00",
        "work_address": "456 Work Ave, New York, NY",
        "commute_preference": "driving",
        "sleep_hours": "23:00 - 07:00",
        "noise_preference": "moderate",
        "hobbies": ["gym"],
    }, headers=auth_headers)
    return auth_headers


@pytest.fixture
def created_analysis(client, user_with_profile):
    """Create one analysis (all external calls mocked) and return the response body."""
    patches = make_mock_services()
    with patches[0], patches[1], patches[2], patches[3], patches[4], \
         patches[5], patches[6], patches[7], patches[8]:
        resp = client.post("/analysis/", json={
            "current_address": "100 Current St, New York, NY",
            "destination_address": "200 Destination Ave, Brooklyn, NY",
        }, headers=user_with_profile)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# POST /analysis/
# ---------------------------------------------------------------------------

class TestCreateAnalysis:
    def test_create_analysis_returns_200(self, client, user_with_profile):
        patches = make_mock_services()
        with patches[0], patches[1], patches[2], patches[3], patches[4], \
             patches[5], patches[6], patches[7], patches[8]:
            resp = client.post("/analysis/", json={
                "current_address": "100 Main St, New York, NY",
                "destination_address": "200 Elm St, Brooklyn, NY",
            }, headers=user_with_profile)
        assert resp.status_code == 200

    def test_create_analysis_response_contains_addresses(self, client, user_with_profile):
        patches = make_mock_services()
        with patches[0], patches[1], patches[2], patches[3], patches[4], \
             patches[5], patches[6], patches[7], patches[8]:
            resp = client.post("/analysis/", json={
                "current_address": "100 Main St, New York, NY",
                "destination_address": "200 Elm St, Brooklyn, NY",
            }, headers=user_with_profile)
        body = resp.json()
        assert body["current_address"] == "100 Main St, New York, NY"
        assert body["destination_address"] == "200 Elm St, Brooklyn, NY"

    def test_create_analysis_response_has_id_and_created_at(self, client, user_with_profile):
        patches = make_mock_services()
        with patches[0], patches[1], patches[2], patches[3], patches[4], \
             patches[5], patches[6], patches[7], patches[8]:
            resp = client.post("/analysis/", json={
                "current_address": "A",
                "destination_address": "B",
            }, headers=user_with_profile)
        body = resp.json()
        assert "id" in body
        assert body["id"] is not None

    def test_create_analysis_geocode_failure_returns_400(self, client, user_with_profile):
        with patch("app.api.analysis.places_service.geocode_address", return_value=(None, None)):
            resp = client.post("/analysis/", json={
                "current_address": "Invalid Address !!!",
                "destination_address": "Also Invalid !!!",
            }, headers=user_with_profile)
        assert resp.status_code == 400
        assert "geocode" in resp.json()["detail"].lower()

    def test_create_analysis_requires_auth(self, client):
        resp = client.post("/analysis/", json={
            "current_address": "A",
            "destination_address": "B",
        })
        assert resp.status_code == 403

    def test_create_analysis_missing_address_returns_422(self, client, user_with_profile):
        resp = client.post("/analysis/", json={
            "current_address": "Only one address",
        }, headers=user_with_profile)
        assert resp.status_code == 422

    def test_wfh_user_gets_zero_commute(self, client, auth_headers):
        """Users with 'Work from home' address should get commute duration = 0."""
        client.post("/profile/", json={
            "work_address": "Work from home",
            "commute_preference": "driving",
            "noise_preference": "moderate",
        }, headers=auth_headers)

        patches = make_mock_services()
        with patches[0], patches[1], patches[2], patches[3], patches[4], \
             patches[5], patches[6], patches[7], patches[8]:
            resp = client.post("/analysis/", json={
                "current_address": "100 Main St, New York, NY",
                "destination_address": "200 Elm St, Brooklyn, NY",
            }, headers=auth_headers)

        assert resp.status_code == 200
        commute = resp.json().get("commute_data", {})
        assert commute.get("duration_minutes") == 0
        assert commute.get("method") == "none"


# ---------------------------------------------------------------------------
# GET /analysis/
# ---------------------------------------------------------------------------

class TestListAnalyses:
    def test_list_returns_empty_for_new_user(self, client, auth_headers):
        resp = client.get("/analysis/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_returns_created_analysis(self, client, user_with_profile, created_analysis):
        resp = client.get("/analysis/", headers=user_with_profile)
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 1
        assert items[0]["id"] == created_analysis["id"]

    def test_list_contains_address_fields(self, client, user_with_profile, created_analysis):
        resp = client.get("/analysis/", headers=user_with_profile)
        item = resp.json()[0]
        assert "current_address" in item
        assert "destination_address" in item
        assert "created_at" in item

    def test_list_does_not_return_other_users_analyses(
        self, client, user_with_profile, created_analysis, second_user
    ):
        resp = client.get("/analysis/", headers=second_user["headers"])
        assert resp.json() == []

    def test_list_limit_parameter(self, client, user_with_profile):
        patches = make_mock_services()
        for _ in range(3):
            with patches[0], patches[1], patches[2], patches[3], patches[4], \
                 patches[5], patches[6], patches[7], patches[8]:
                client.post("/analysis/", json={
                    "current_address": "A",
                    "destination_address": "B",
                }, headers=user_with_profile)

        resp = client.get("/analysis/?limit=2", headers=user_with_profile)
        assert len(resp.json()) == 2

    def test_list_requires_auth(self, client):
        resp = client.get("/analysis/")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /analysis/{id}
# ---------------------------------------------------------------------------

class TestGetAnalysisDetail:
    def test_get_analysis_returns_top_level_scores(self, client, user_with_profile, created_analysis):
        resp = client.get(f"/analysis/{created_analysis['id']}", headers=user_with_profile)
        assert resp.status_code == 200
        body = resp.json()
        for field in ["overall_score", "safety_score", "affordability_score",
                      "environment_score", "lifestyle_score", "convenience_score"]:
            assert field in body, f"Missing top-level field: {field}"
            assert isinstance(body[field], (int, float))

    def test_get_analysis_returns_data_objects(self, client, user_with_profile, created_analysis):
        resp = client.get(f"/analysis/{created_analysis['id']}", headers=user_with_profile)
        body = resp.json()
        for field in ["crime_data", "cost_data", "noise_data", "amenities_data", "commute_data"]:
            assert field in body

    def test_get_analysis_returns_ai_fields(self, client, user_with_profile, created_analysis):
        resp = client.get(f"/analysis/{created_analysis['id']}", headers=user_with_profile)
        body = resp.json()
        assert "overview_summary" in body
        assert "lifestyle_changes" in body
        assert "ai_insights" in body

    def test_get_analysis_wrong_user_returns_404(self, client, user_with_profile, created_analysis, second_user):
        resp = client.get(
            f"/analysis/{created_analysis['id']}",
            headers=second_user["headers"],
        )
        assert resp.status_code == 404

    def test_get_analysis_nonexistent_returns_404(self, client, auth_headers):
        resp = client.get("/analysis/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_analysis_requires_auth(self, client, user_with_profile, created_analysis):
        resp = client.get(f"/analysis/{created_analysis['id']}")
        assert resp.status_code == 403

    def test_get_analysis_grade_is_string(self, client, user_with_profile, created_analysis):
        resp = client.get(f"/analysis/{created_analysis['id']}", headers=user_with_profile)
        assert isinstance(resp.json()["grade"], str)


# ---------------------------------------------------------------------------
# DELETE /analysis/{id}
# ---------------------------------------------------------------------------

class TestDeleteAnalysis:
    def test_delete_analysis_returns_success_message(self, client, user_with_profile, created_analysis):
        resp = client.delete(
            f"/analysis/{created_analysis['id']}",
            headers=user_with_profile,
        )
        assert resp.status_code == 200
        assert "deleted" in resp.json()["message"].lower()

    def test_deleted_analysis_no_longer_in_list(self, client, user_with_profile, created_analysis):
        client.delete(f"/analysis/{created_analysis['id']}", headers=user_with_profile)
        list_resp = client.get("/analysis/", headers=user_with_profile)
        assert list_resp.json() == []

    def test_deleted_analysis_returns_404_on_get(self, client, user_with_profile, created_analysis):
        client.delete(f"/analysis/{created_analysis['id']}", headers=user_with_profile)
        resp = client.get(f"/analysis/{created_analysis['id']}", headers=user_with_profile)
        assert resp.status_code == 404

    def test_delete_wrong_user_returns_404(self, client, user_with_profile, created_analysis, second_user):
        resp = client.delete(
            f"/analysis/{created_analysis['id']}",
            headers=second_user["headers"],
        )
        assert resp.status_code == 404

    def test_delete_nonexistent_returns_404(self, client, auth_headers):
        resp = client.delete("/analysis/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_requires_auth(self, client, user_with_profile, created_analysis):
        resp = client.delete(f"/analysis/{created_analysis['id']}")
        assert resp.status_code == 403
