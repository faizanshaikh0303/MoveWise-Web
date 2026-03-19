"""Integration tests for /analysis endpoints (GET, DELETE, list).

The POST /analysis endpoint is excluded because it fans out to multiple
external APIs (Google Maps, FBI, LLM, etc.) that would require heavy mocking.
"""
import json
import pytest
from datetime import datetime, timezone, timedelta
from app.models.analysis import Analysis
from app.core.security import create_access_token


def make_analysis(db, user_id, **kwargs):
    """Helper: create and commit a minimal Analysis row."""
    defaults = {
        "current_address": "123 Main St",
        "destination_address": "456 Oak Ave",
    }
    a = Analysis(user_id=user_id, **{**defaults, **kwargs})
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


class TestListAnalyses:
    def test_empty_list_for_new_user(self, client, test_user, auth_headers):
        resp = client.get("/analysis/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_own_analyses(self, client, test_user, auth_headers, analysis):
        resp = client.get("/analysis/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == analysis.id

    def test_ordered_newest_first(self, client, test_user, auth_headers, db):
        make_analysis(db, test_user.id,
                      current_address="Old",
                      created_at=datetime.now(timezone.utc) - timedelta(hours=2))
        make_analysis(db, test_user.id,
                      current_address="New",
                      created_at=datetime.now(timezone.utc))

        resp = client.get("/analysis/", headers=auth_headers)
        data = resp.json()
        assert data[0]["current_address"] == "New"
        assert data[1]["current_address"] == "Old"

    def test_limit_parameter(self, client, test_user, auth_headers, db):
        for i in range(5):
            make_analysis(db, test_user.id, current_address=f"Addr {i}")
        resp = client.get("/analysis/?limit=3", headers=auth_headers)
        assert len(resp.json()) == 3

    def test_does_not_expose_other_users_analyses(self, client, test_user, auth_headers, db):
        # Insert an analysis belonging to a non-existent / different user
        make_analysis(db, test_user.id + 9999, current_address="Intruder")
        resp = client.get("/analysis/", headers=auth_headers)
        for item in resp.json():
            assert item["current_address"] != "Intruder"

    def test_no_auth_returns_403(self, client):
        resp = client.get("/analysis/")
        assert resp.status_code == 403


class TestGetAnalysis:
    def test_returns_full_response(self, client, test_user, auth_headers, analysis):
        resp = client.get(f"/analysis/{analysis.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == analysis.id
        assert data["current_address"] == "123 Main St, New York, NY"
        assert data["destination_address"] == "456 Oak Ave, Los Angeles, CA"

    def test_scores_returned_at_top_level(self, client, test_user, auth_headers, analysis):
        data = client.get(f"/analysis/{analysis.id}", headers=auth_headers).json()
        assert data["overall_score"] == 75.5
        assert data["safety_score"] == 80.0
        assert data["affordability_score"] == 70.0
        assert data["environment_score"] == 75.0
        assert data["lifestyle_score"] == 72.0
        assert data["convenience_score"] == 68.0
        assert data["grade"] == "B+"

    def test_action_steps_parsed_from_json(self, client, test_user, auth_headers, analysis):
        data = client.get(f"/analysis/{analysis.id}", headers=auth_headers).json()
        assert data["action_steps"] == ["Research neighborhoods", "Visit the city"]

    def test_action_steps_null_returns_empty_list(self, client, test_user, auth_headers, db):
        a = make_analysis(db, test_user.id, action_steps_json=None)
        data = client.get(f"/analysis/{a.id}", headers=auth_headers).json()
        assert data["action_steps"] == []

    def test_action_steps_empty_json_array(self, client, test_user, auth_headers, db):
        a = make_analysis(db, test_user.id, action_steps_json="[]")
        data = client.get(f"/analysis/{a.id}", headers=auth_headers).json()
        assert data["action_steps"] == []

    def test_action_steps_multiple_items(self, client, test_user, auth_headers, db):
        steps = ["Step 1", "Step 2", "Step 3"]
        a = make_analysis(db, test_user.id, action_steps_json=json.dumps(steps))
        data = client.get(f"/analysis/{a.id}", headers=auth_headers).json()
        assert data["action_steps"] == steps

    def test_null_scores_return_zero(self, client, test_user, auth_headers, db):
        a = make_analysis(db, test_user.id,
                          overall_weighted_score=None,
                          crime_safety_score=None,
                          cost_affordability_score=None,
                          noise_environment_score=None,
                          lifestyle_score=None,
                          convenience_score=None)
        data = client.get(f"/analysis/{a.id}", headers=auth_headers).json()
        assert data["overall_score"] == 0.0
        assert data["safety_score"] == 0.0
        assert data["affordability_score"] == 0.0
        assert data["environment_score"] == 0.0
        assert data["lifestyle_score"] == 0.0
        assert data["convenience_score"] == 0.0

    def test_null_overview_returns_default_message(self, client, test_user, auth_headers, db):
        a = make_analysis(db, test_user.id, overview_summary=None)
        data = client.get(f"/analysis/{a.id}", headers=auth_headers).json()
        assert data["overview_summary"] == "Analysis complete."

    def test_null_lifestyle_changes_returns_empty_list(self, client, test_user, auth_headers, db):
        a = make_analysis(db, test_user.id, lifestyle_changes=None)
        data = client.get(f"/analysis/{a.id}", headers=auth_headers).json()
        assert data["lifestyle_changes"] == []

    def test_null_ai_insights_returns_empty_string(self, client, test_user, auth_headers, db):
        a = make_analysis(db, test_user.id, ai_insights=None)
        data = client.get(f"/analysis/{a.id}", headers=auth_headers).json()
        assert data["ai_insights"] == ""

    def test_null_data_objects_return_empty_dicts(self, client, test_user, auth_headers, db):
        a = make_analysis(db, test_user.id,
                          crime_data=None, cost_data=None,
                          noise_data=None, amenities_data=None, commute_data=None)
        data = client.get(f"/analysis/{a.id}", headers=auth_headers).json()
        assert data["crime_data"] == {}
        assert data["cost_data"] == {}
        assert data["noise_data"] == {}
        assert data["amenities_data"] == {}
        assert data["commute_data"] == {}

    def test_created_at_is_returned(self, client, test_user, auth_headers, analysis):
        data = client.get(f"/analysis/{analysis.id}", headers=auth_headers).json()
        assert data["created_at"] is not None

    def test_nonexistent_id_returns_404(self, client, test_user, auth_headers):
        resp = client.get("/analysis/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_other_users_analysis_returns_404(self, client, test_user, db):
        other_analysis = make_analysis(db, test_user.id + 9999)
        token = create_access_token(data={"sub": test_user.email})
        resp = client.get(f"/analysis/{other_analysis.id}",
                          headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404

    def test_no_auth_returns_403(self, client, analysis):
        resp = client.get(f"/analysis/{analysis.id}")
        assert resp.status_code == 403


class TestDeleteAnalysis:
    def test_delete_success(self, client, test_user, auth_headers, analysis):
        resp = client.delete(f"/analysis/{analysis.id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["message"] == "Analysis deleted successfully"

    def test_deleted_analysis_no_longer_accessible(self, client, test_user, auth_headers, analysis):
        client.delete(f"/analysis/{analysis.id}", headers=auth_headers)
        resp = client.get(f"/analysis/{analysis.id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_deleted_analysis_absent_from_list(self, client, test_user, auth_headers, analysis):
        client.delete(f"/analysis/{analysis.id}", headers=auth_headers)
        ids = [item["id"] for item in client.get("/analysis/", headers=auth_headers).json()]
        assert analysis.id not in ids

    def test_delete_nonexistent_returns_404(self, client, test_user, auth_headers):
        resp = client.delete("/analysis/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_other_users_analysis_returns_404(self, client, test_user, db):
        other_analysis = make_analysis(db, test_user.id + 9999)
        token = create_access_token(data={"sub": test_user.email})
        resp = client.delete(f"/analysis/{other_analysis.id}",
                             headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404

    def test_no_auth_returns_403(self, client, analysis):
        resp = client.delete(f"/analysis/{analysis.id}")
        assert resp.status_code == 403
