"""Unit tests for LLMService — mocked Groq client."""
import pytest
from unittest.mock import MagicMock, patch
from app.services.llm_service import LLMService


@pytest.fixture
def svc():
    return LLMService()


SAMPLE_DATA = {
    "crime_data": {
        "current": {"total_crimes": 50, "daily_average": 1.7, "safety_score": 70,
                    "crime_rate_per_100k": 3500, "categories": {"violent": 10, "larceny": 24,
                    "burglary": 7, "other_property": 7}, "temporal_analysis": {
                    "crimes_during_sleep_hours": 15, "crimes_during_work_hours": 20,
                    "crimes_during_commute": 8, "peak_hours": [19, 20, 21]}},
        "destination": {"total_crimes": 35, "daily_average": 1.2, "safety_score": 80,
                        "crime_rate_per_100k": 2331, "categories": {"violent": 7, "larceny": 17,
                        "burglary": 5, "other_property": 4}, "temporal_analysis": {
                        "crimes_during_sleep_hours": 10, "crimes_during_work_hours": 14,
                        "crimes_during_commute": 6, "peak_hours": [20, 21]}},
        "comparison": {"crime_difference": -15, "score_difference": 10.0,
                       "recommendation": "Destination is safer."},
    },
    "noise_data": {
        "current": {"estimated_db": 65.0, "noise_category": "Noisy", "noise_score": 60,
                    "description": "Moderate traffic"},
        "destination": {"estimated_db": 55.0, "noise_category": "Moderate", "noise_score": 75,
                        "description": "Moderate", "preference_match": {"quality": "balanced"}},
        "comparison": {"db_difference": -10.0, "score_difference": 15.0, "is_quieter": True,
                       "recommendation": "Quieter", "preference_match": {"quality": "balanced"}},
    },
    "cost_data": {
        "current": {"total_monthly": 3000, "total_annual": 36000, "affordability_score": 80,
                    "cost_index": 1.0, "housing": {"monthly_rent": 1050},
                    "expenses": {"utilities": 300, "groceries": 450, "transportation": 450,
                                 "healthcare": 300, "entertainment": 240}},
        "destination": {"total_monthly": 2500, "total_annual": 30000, "affordability_score": 85,
                        "cost_index": 0.83, "housing": {"monthly_rent": 875},
                        "expenses": {"utilities": 250, "groceries": 375, "transportation": 375,
                                     "healthcare": 250, "entertainment": 200}},
        "comparison": {"monthly_difference": -500, "annual_difference": -6000,
                       "percent_change": -16.7, "recommendation": "Great savings!"},
    },
    "amenities_data": {
        "destination": {"total_count": 25, "by_type": {"grocery stores": 5, "parks": 8}},
    },
    "commute_data": {"duration_minutes": 25, "method": "driving", "distance": "12 miles"},
    "user_preferences": {"work_hours": "9:00 - 17:00", "sleep_hours": "23:00 - 07:00",
                         "noise_preference": "moderate", "hobbies": ["gym", "hiking"]},
    "overall_scores": {
        "overall_score": 78.5, "grade": "B+",
        "component_scores": {
            "safety": {"score": 80}, "affordability": {"score": 85},
            "environment": {"score": 75}, "lifestyle": {"score": 72},
            "convenience": {"score": 68},
        },
        "strengths": ["Safety", "Affordability"],
        "concerns": [{"area": "Convenience", "score": 55}],
    },
}

WELL_FORMED_LLM_RESPONSE = """
---OVERVIEW---
This is a good move overall with improved safety and lower costs.

---LIFESTYLE_CHANGES---
✓ Safety improves with 30% fewer crimes at destination
✓ Cost of living decreases by $500/month
✓ Noise levels are quieter (55 dB vs 65 dB)
✓ Commute of 25 minutes by driving
✓ 25 nearby amenities including parks
✓ Better affordability score (85 vs 80)

---INSIGHTS---
The destination offers a great combination of improved safety and reduced costs.
You will save $6,000 per year which is significant.

---ACTION_STEPS---
→ Visit the destination during peak hours (8pm-9pm) to assess the neighborhood
→ Budget for the move, factoring in $500/month savings
→ Research local gyms and hiking trails near the destination
→ Contact local utilities to compare rates
→ Schedule a weekend visit before committing
"""


# ── _parse_llm_response ───────────────────────────────────────────────────────

class TestParseLlmResponse:
    def test_parses_overview(self, svc):
        result = svc._parse_llm_response(WELL_FORMED_LLM_RESPONSE)
        assert "good move" in result["overview_summary"].lower()

    def test_parses_lifestyle_changes(self, svc):
        result = svc._parse_llm_response(WELL_FORMED_LLM_RESPONSE)
        assert len(result["lifestyle_changes"]) == 6

    def test_lifestyle_changes_have_checkmark(self, svc):
        result = svc._parse_llm_response(WELL_FORMED_LLM_RESPONSE)
        for change in result["lifestyle_changes"]:
            assert "✓" in change

    def test_parses_insights(self, svc):
        result = svc._parse_llm_response(WELL_FORMED_LLM_RESPONSE)
        assert "destination" in result["ai_insights"].lower()

    def test_parses_action_steps(self, svc):
        result = svc._parse_llm_response(WELL_FORMED_LLM_RESPONSE)
        assert len(result["action_steps"]) == 5

    def test_action_steps_have_arrow(self, svc):
        result = svc._parse_llm_response(WELL_FORMED_LLM_RESPONSE)
        for step in result["action_steps"]:
            assert "→" in step

    def test_max_6_lifestyle_changes(self, svc):
        many_changes = "\n".join(f"✓ Change {i}" for i in range(10))
        response = f"---OVERVIEW---\nSome overview.\n---LIFESTYLE_CHANGES---\n{many_changes}\n---INSIGHTS---\nInsights.\n---ACTION_STEPS---\n"
        result = svc._parse_llm_response(response)
        assert len(result["lifestyle_changes"]) <= 6

    def test_max_7_action_steps(self, svc):
        many_steps = "\n".join(f"→ Step {i}" for i in range(10))
        response = f"---OVERVIEW---\nOverview.\n---LIFESTYLE_CHANGES---\n✓ change\n---INSIGHTS---\nInsights.\n---ACTION_STEPS---\n{many_steps}"
        result = svc._parse_llm_response(response)
        assert len(result["action_steps"]) <= 7

    def test_empty_response_returns_defaults(self, svc):
        result = svc._parse_llm_response("")
        assert "overview_summary" in result
        assert "lifestyle_changes" in result
        assert "ai_insights" in result
        assert "action_steps" in result

    def test_missing_sections_return_empty(self, svc):
        result = svc._parse_llm_response("Plain text with no delimiters.")
        assert isinstance(result["lifestyle_changes"], list)
        assert isinstance(result["action_steps"], list)

    def test_returns_all_required_keys(self, svc):
        result = svc._parse_llm_response(WELL_FORMED_LLM_RESPONSE)
        for key in ("overview_summary", "lifestyle_changes", "ai_insights", "action_steps"):
            assert key in result


# ── _build_analysis_prompt ────────────────────────────────────────────────────

class TestBuildAnalysisPrompt:
    def test_contains_addresses(self, svc):
        prompt = svc._build_analysis_prompt(
            "New York, NY", "Los Angeles, CA", **{k: SAMPLE_DATA[k] for k in
            ["crime_data", "amenities_data", "cost_data", "noise_data", "commute_data"]}
        )
        assert "New York, NY" in prompt
        assert "Los Angeles, CA" in prompt

    def test_contains_crime_data(self, svc):
        prompt = svc._build_analysis_prompt(
            "A", "B", **{k: SAMPLE_DATA[k] for k in
            ["crime_data", "amenities_data", "cost_data", "noise_data", "commute_data"]}
        )
        assert "Safety Score" in prompt
        assert "Crime" in prompt

    def test_contains_cost_data(self, svc):
        prompt = svc._build_analysis_prompt(
            "A", "B", **{k: SAMPLE_DATA[k] for k in
            ["crime_data", "amenities_data", "cost_data", "noise_data", "commute_data"]}
        )
        assert "Total Monthly" in prompt

    def test_includes_user_preferences_when_provided(self, svc):
        prompt = svc._build_analysis_prompt(
            "A", "B",
            crime_data=SAMPLE_DATA["crime_data"],
            amenities_data=SAMPLE_DATA["amenities_data"],
            cost_data=SAMPLE_DATA["cost_data"],
            noise_data=SAMPLE_DATA["noise_data"],
            commute_data=SAMPLE_DATA["commute_data"],
            user_preferences=SAMPLE_DATA["user_preferences"],
        )
        assert "Work Schedule" in prompt
        assert "gym" in prompt.lower()

    def test_excludes_user_preferences_section_when_none(self, svc):
        prompt = svc._build_analysis_prompt(
            "A", "B",
            crime_data=SAMPLE_DATA["crime_data"],
            amenities_data=SAMPLE_DATA["amenities_data"],
            cost_data=SAMPLE_DATA["cost_data"],
            noise_data=SAMPLE_DATA["noise_data"],
            commute_data=SAMPLE_DATA["commute_data"],
            user_preferences=None,
        )
        assert "Work Schedule" not in prompt

    def test_includes_overall_scores_when_provided(self, svc):
        prompt = svc._build_analysis_prompt(
            "A", "B",
            crime_data=SAMPLE_DATA["crime_data"],
            amenities_data=SAMPLE_DATA["amenities_data"],
            cost_data=SAMPLE_DATA["cost_data"],
            noise_data=SAMPLE_DATA["noise_data"],
            commute_data=SAMPLE_DATA["commute_data"],
            overall_scores=SAMPLE_DATA["overall_scores"],
        )
        assert "Overall Score" in prompt
        assert "B+" in prompt

    def test_amenity_types_listed(self, svc):
        prompt = svc._build_analysis_prompt(
            "A", "B",
            crime_data=SAMPLE_DATA["crime_data"],
            amenities_data={"destination": {"total_count": 13, "by_type": {"parks": 8, "grocery stores": 5}}},
            cost_data=SAMPLE_DATA["cost_data"],
            noise_data=SAMPLE_DATA["noise_data"],
            commute_data=SAMPLE_DATA["commute_data"],
        )
        assert "Parks" in prompt or "parks" in prompt

    def test_returns_string(self, svc):
        prompt = svc._build_analysis_prompt(
            "A", "B", **{k: SAMPLE_DATA[k] for k in
            ["crime_data", "amenities_data", "cost_data", "noise_data", "commute_data"]}
        )
        assert isinstance(prompt, str)
        assert len(prompt) > 100


# ── generate_lifestyle_analysis ───────────────────────────────────────────────

class TestGenerateLifestyleAnalysis:
    def _mock_groq_response(self, text):
        msg = MagicMock()
        msg.content = text
        choice = MagicMock()
        choice.message = msg
        completion = MagicMock()
        completion.choices = [choice]
        return completion

    def test_success_returns_parsed_result(self, svc):
        svc.client.chat.completions.create.return_value = self._mock_groq_response(
            WELL_FORMED_LLM_RESPONSE
        )
        result = svc.generate_lifestyle_analysis(
            "New York, NY", "Los Angeles, CA",
            SAMPLE_DATA["crime_data"], SAMPLE_DATA["amenities_data"],
            SAMPLE_DATA["cost_data"], SAMPLE_DATA["noise_data"],
            SAMPLE_DATA["commute_data"],
        )
        assert "overview_summary" in result
        assert "lifestyle_changes" in result
        assert "action_steps" in result

    def test_api_exception_returns_fallback(self, svc):
        svc.client.chat.completions.create.side_effect = Exception("API error")
        result = svc.generate_lifestyle_analysis(
            "New York, NY", "Los Angeles, CA",
            SAMPLE_DATA["crime_data"], SAMPLE_DATA["amenities_data"],
            SAMPLE_DATA["cost_data"], SAMPLE_DATA["noise_data"],
            SAMPLE_DATA["commute_data"],
        )
        assert result["lifestyle_changes"] == []
        assert result["action_steps"] == []
        assert "temporarily unavailable" in result["overview_summary"].lower()

    def test_with_user_preferences(self, svc):
        svc.client.chat.completions.create.return_value = self._mock_groq_response(
            WELL_FORMED_LLM_RESPONSE
        )
        result = svc.generate_lifestyle_analysis(
            "A", "B",
            SAMPLE_DATA["crime_data"], SAMPLE_DATA["amenities_data"],
            SAMPLE_DATA["cost_data"], SAMPLE_DATA["noise_data"],
            SAMPLE_DATA["commute_data"],
            user_preferences=SAMPLE_DATA["user_preferences"],
            overall_scores=SAMPLE_DATA["overall_scores"],
        )
        assert isinstance(result, dict)
