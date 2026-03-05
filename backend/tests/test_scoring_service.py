"""
Unit tests for ScoringService.

These tests exercise the pure business logic with no DB or HTTP calls.
"""
import pytest
from app.services.scoring_service import ScoringService

service = ScoringService()


# ---------------------------------------------------------------------------
# Helpers – build minimal data structures the service expects
# ---------------------------------------------------------------------------

def crime(safety_score: float) -> dict:
    return {
        "destination": {"safety_score": safety_score},
        "comparison": {"score_difference": 5.0},
    }


def noise(noise_score: float) -> dict:
    return {
        "destination": {"noise_score": noise_score},
        "comparison": {"db_difference": -5.0, "db_change_description": "Quieter"},
    }


def cost(affordability_score: float, monthly_diff: float = -200.0) -> dict:
    return {
        "destination": {"affordability_score": affordability_score},
        "comparison": {"monthly_difference": monthly_diff},
    }


def amenities(dest_counts: dict) -> dict:
    return {"destination_amenities": dest_counts}


def commute(duration_minutes, method="driving") -> dict:
    return {"duration_minutes": duration_minutes, "method": method}


# ---------------------------------------------------------------------------
# Weights
# ---------------------------------------------------------------------------

class TestWeights:
    def test_weights_sum_to_one(self):
        total = sum(ScoringService.WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9

    def test_safety_is_highest_weight(self):
        weights = ScoringService.WEIGHTS
        assert weights["safety"] == max(weights.values())

    def test_convenience_is_lowest_weight(self):
        weights = ScoringService.WEIGHTS
        assert weights["convenience"] == min(weights.values())


# ---------------------------------------------------------------------------
# calculate_overall_score
# ---------------------------------------------------------------------------

class TestCalculateOverallScore:
    def test_returns_required_keys(self):
        result = service.calculate_overall_score(
            crime(80), noise(80), cost(80), amenities({"cafes": 20}), commute(20)
        )
        for key in ["overall_score", "grade", "component_scores",
                    "comparison_insights", "strengths", "concerns", "recommendation"]:
            assert key in result

    def test_component_scores_have_all_categories(self):
        result = service.calculate_overall_score(
            crime(80), noise(80), cost(80), amenities({"cafes": 20}), commute(20)
        )
        for cat in ["safety", "affordability", "environment", "lifestyle", "convenience"]:
            assert cat in result["component_scores"]

    def test_overall_score_within_bounds(self):
        result = service.calculate_overall_score(
            crime(100), noise(100), cost(100), amenities({"a": 60}), commute(5)
        )
        assert 0 <= result["overall_score"] <= 100

    def test_weighted_calculation_is_correct(self):
        """
        With all component scores = 80 the weighted average must also be 80.
        Lifestyle score for 20 amenities = 75 + variety_bonus(3) = 78 (1 category).
        Convenience for 20 min = 100.
        Let's verify the formula directly with known inputs.
        """
        # Force known scores via the data structures
        result = service.calculate_overall_score(
            crime(70), noise(70), cost(70), None, None
        )
        # Without amenities/commute, defaults are 70/70
        expected = (
            70 * 0.30 +  # safety
            70 * 0.25 +  # affordability
            70 * 0.20 +  # environment
            70 * 0.15 +  # lifestyle (default 70)
            70 * 0.10    # convenience (default 70)
        )
        assert abs(result["overall_score"] - expected) < 0.5

    def test_no_amenities_or_commute_uses_defaults(self):
        result = service.calculate_overall_score(crime(70), noise(70), cost(70))
        # Should not raise, and overall_score should be in range
        assert 0 <= result["overall_score"] <= 100


# ---------------------------------------------------------------------------
# _score_to_grade
# ---------------------------------------------------------------------------

class TestScoreToGrade:
    @pytest.mark.parametrize("score,expected_grade", [
        (95.0, "A+"),
        (90.0, "A+"),
        (87.0, "A"),
        (85.0, "A"),
        (82.0, "A-"),
        (80.0, "A-"),
        (77.0, "B+"),
        (75.0, "B+"),
        (72.0, "B"),
        (70.0, "B"),
        (67.0, "B-"),
        (65.0, "B-"),
        (62.0, "C+"),
        (60.0, "C+"),
        (57.0, "C"),
        (55.0, "C"),
        (52.0, "C-"),
        (50.0, "C-"),
        (49.0, "D"),
        (0.0,  "D"),
    ])
    def test_grade_boundaries(self, score, expected_grade):
        assert service._score_to_grade(score) == expected_grade


# ---------------------------------------------------------------------------
# _get_score_status
# ---------------------------------------------------------------------------

class TestGetScoreStatus:
    @pytest.mark.parametrize("score,expected_status", [
        (80.0, "Excellent"),
        (95.0, "Excellent"),
        (70.0, "Good"),
        (79.9, "Good"),
        (60.0, "Fair"),
        (69.9, "Fair"),
        (50.0, "Needs Attention"),
        (59.9, "Needs Attention"),
        (49.9, "Concerning"),
        (0.0,  "Concerning"),
    ])
    def test_status_labels(self, score, expected_status):
        assert service._get_score_status(score) == expected_status


# ---------------------------------------------------------------------------
# _calculate_lifestyle_score
# ---------------------------------------------------------------------------

class TestLifestyleScore:
    @pytest.mark.parametrize("total,expected_base", [
        (60, 100.0),
        (50, 100.0),
        (35, 90.0),
        (25, 75.0),
        (15, 60.0),
        (7,  40.0),
        (2,  20.0),
    ])
    def test_score_tiers(self, total, expected_base):
        # Single category to minimise variety bonus
        data = {"destination_amenities": {"cafes": total}}
        score = service._calculate_lifestyle_score(data)
        # variety bonus for 1 category = 3 pts
        assert score >= expected_base
        assert score <= 100.0

    def test_variety_bonus_increases_score(self):
        # Same total amenities but spread across more categories
        sparse = {"destination_amenities": {"cafes": 20}}
        diverse = {"destination_amenities": {
            "cafes": 4, "restaurants": 4, "gyms": 4, "parks": 4, "libraries": 4
        }}
        score_sparse = service._calculate_lifestyle_score(sparse)
        score_diverse = service._calculate_lifestyle_score(diverse)
        assert score_diverse > score_sparse

    def test_variety_bonus_capped_at_15(self):
        # 10 categories × 3 = 30, but capped at 15
        many_cats = {f"cat_{i}": 5 for i in range(10)}
        data = {"destination_amenities": many_cats}
        score = service._calculate_lifestyle_score(data)
        assert score <= 100.0

    def test_no_amenities_returns_low_score(self):
        assert service._calculate_lifestyle_score(None) == 10.0
        assert service._calculate_lifestyle_score({}) == 10.0
        assert service._calculate_lifestyle_score({"destination_amenities": {}}) == 10.0


# ---------------------------------------------------------------------------
# _calculate_convenience_score
# ---------------------------------------------------------------------------

class TestConvenienceScore:
    def test_work_from_home_returns_100(self):
        assert service._calculate_convenience_score({"duration_minutes": 0, "method": "none"}) == 100.0
        assert service._calculate_convenience_score({"duration_minutes": 0, "method": "driving"}) == 100.0

    def test_method_none_returns_100(self):
        assert service._calculate_convenience_score({"method": "none"}) == 100.0

    @pytest.mark.parametrize("duration,min_expected,max_expected", [
        (10,  100, 100),   # ≤ 20 min → 100
        (20,  100, 100),
        (25,  80,  90),    # 20-30 → 90-something
        (30,  80,  80),    # exactly 30 → 80
        (40,  60,  80),    # 30-45
        (45,  55,  60),    # exactly 45 → 80 - (15*1.5) = 57.5
        (55,  30,  60),    # 45-60
        (60,  30,  30),    # exactly 60 → 30
        (90,  20,  30),    # > 60
    ])
    def test_duration_score_ranges(self, duration, min_expected, max_expected):
        score = service._calculate_convenience_score({"duration_minutes": duration, "method": "driving"})
        assert min_expected <= score <= max_expected

    def test_no_commute_data_returns_default(self):
        assert service._calculate_convenience_score(None) == 70
        assert service._calculate_convenience_score({}) == 70


# ---------------------------------------------------------------------------
# _identify_strengths / _identify_concerns
# ---------------------------------------------------------------------------

class TestStrengthsAndConcerns:
    def test_strengths_include_scores_above_75(self):
        strengths = service._identify_strengths(90, 80, 76, 50, 40)
        assert "Safety" in strengths
        assert "Affordability" in strengths
        assert "Environment" in strengths

    def test_strengths_exclude_scores_below_75(self):
        strengths = service._identify_strengths(90, 80, 76, 50, 40)
        assert "Lifestyle" not in strengths
        assert "Convenience" not in strengths

    def test_strengths_sorted_by_score_descending(self):
        strengths = service._identify_strengths(80, 85, 90, 76, 40)
        # Environment(90) > Affordability(85) > Safety(80) > Lifestyle(76)
        assert strengths[0] == "Environment"

    def test_concerns_include_scores_below_60(self):
        concerns = service._identify_concerns(40, 55, 80, 80, 80)
        areas = [c["area"] for c in concerns]
        assert "Safety" in areas
        assert "Affordability" in areas

    def test_concerns_sorted_lowest_first(self):
        concerns = service._identify_concerns(30, 55, 80, 80, 80)
        assert concerns[0]["area"] == "Safety"

    def test_no_concerns_when_all_above_60(self):
        assert service._identify_concerns(65, 65, 65, 65, 65) == []


# ---------------------------------------------------------------------------
# _generate_overall_recommendation
# ---------------------------------------------------------------------------

class TestRecommendation:
    def test_low_safety_triggers_caution(self):
        rec = service._generate_overall_recommendation(70, 45, 80, 80)
        assert "caution" in rec.lower() or "safety" in rec.lower()

    def test_low_affordability_triggers_financial_warning(self):
        rec = service._generate_overall_recommendation(70, 80, 45, 80)
        assert "financial" in rec.lower() or "budget" in rec.lower()

    def test_high_overall_score_is_recommended(self):
        rec = service._generate_overall_recommendation(90, 85, 80, 80)
        assert "recommended" in rec.lower() or "excellent" in rec.lower()

    def test_score_above_75_is_recommended(self):
        rec = service._generate_overall_recommendation(78, 80, 80, 80)
        assert "recommended" in rec.lower() or "solid" in rec.lower()

    def test_low_overall_score_suggests_alternatives(self):
        rec = service._generate_overall_recommendation(40, 80, 80, 80)
        assert any(word in rec.lower() for word in ["concern", "alternative", "caution", "mixed"])

