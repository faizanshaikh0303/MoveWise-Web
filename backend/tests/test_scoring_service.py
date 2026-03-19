"""Unit tests for ScoringService — pure Python, no DB or HTTP."""
import pytest
from app.services.scoring_service import ScoringService, scoring_service


# ── Helpers ──────────────────────────────────────────────────────────────────

def crime(score=75):
    return {"destination": {"safety_score": score}}

def cost(score=75):
    return {"destination": {"affordability_score": score}}

def noise(score=75):
    return {"destination": {"noise_score": score}}

def amenities(score=75):
    return {"lifestyle_score": score}

def commute(score=75):
    return {"convenience_score": score}


def full_score(**overrides):
    """Call calculate_overall_score with all five components."""
    kwargs = dict(
        crime_data=crime(overrides.get("safety", 75)),
        cost_data=cost(overrides.get("affordability", 75)),
        noise_data=noise(overrides.get("environment", 75)),
        amenities_data=amenities(overrides.get("lifestyle", 75)),
        commute_data=commute(overrides.get("convenience", 75)),
    )
    return scoring_service.calculate_overall_score(**kwargs)


# ── calculate_overall_score ───────────────────────────────────────────────────

class TestCalculateOverallScore:
    def test_returns_required_top_level_keys(self):
        result = full_score()
        for key in ("overall_score", "grade", "component_scores", "strengths", "concerns"):
            assert key in result

    def test_component_score_keys_present(self):
        result = full_score()
        for key in ("safety", "affordability", "environment", "lifestyle", "convenience"):
            assert key in result["component_scores"]

    def test_each_component_has_score_weight_contribution_status(self):
        result = full_score()
        for comp in result["component_scores"].values():
            assert "score" in comp
            assert "weight" in comp
            assert "contribution" in comp
            assert "status" in comp

    def test_weights_sum_to_one(self):
        total = sum(ScoringService.WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9

    def test_all_100_gives_100(self):
        result = full_score(safety=100, affordability=100, environment=100,
                            lifestyle=100, convenience=100)
        assert result["overall_score"] == 100.0

    def test_all_zero_gives_zero(self):
        result = full_score(safety=0, affordability=0, environment=0,
                            lifestyle=0, convenience=0)
        assert result["overall_score"] == 0.0

    def test_weighted_formula_is_correct(self):
        w = ScoringService.WEIGHTS
        result = full_score(safety=80, affordability=60, environment=70,
                            lifestyle=90, convenience=50)
        expected = round(
            80 * w["safety"] +
            60 * w["affordability"] +
            70 * w["environment"] +
            90 * w["lifestyle"] +
            50 * w["convenience"],
            1,
        )
        assert result["overall_score"] == expected

    def test_only_one_high_score_affects_overall(self):
        result = full_score(safety=100, affordability=0, environment=0,
                            lifestyle=0, convenience=0)
        expected = round(100 * ScoringService.WEIGHTS["safety"], 1)
        assert abs(result["overall_score"] - expected) < 0.1

    def test_missing_amenities_defaults_to_70(self):
        result = scoring_service.calculate_overall_score(
            crime_data=crime(70),
            cost_data=cost(70),
            noise_data=noise(70),
            amenities_data=None,
            commute_data=commute(70),
        )
        assert result["component_scores"]["lifestyle"]["score"] == 70.0

    def test_missing_commute_defaults_to_70(self):
        result = scoring_service.calculate_overall_score(
            crime_data=crime(70),
            cost_data=cost(70),
            noise_data=noise(70),
            commute_data=None,
        )
        assert result["component_scores"]["convenience"]["score"] == 70.0

    def test_missing_both_optional_defaults_to_70(self):
        result = scoring_service.calculate_overall_score(
            crime_data=crime(70),
            cost_data=cost(70),
            noise_data=noise(70),
        )
        assert result["component_scores"]["lifestyle"]["score"] == 70.0
        assert result["component_scores"]["convenience"]["score"] == 70.0

    def test_contribution_equals_score_times_weight(self):
        result = full_score(safety=80, affordability=65, environment=72,
                            lifestyle=88, convenience=55)
        for comp in result["component_scores"].values():
            expected = round(comp["score"] * comp["weight"], 1)
            assert comp["contribution"] == expected

    def test_missing_nested_key_falls_back_to_70(self):
        # crime_data has no 'destination' key at all
        result = scoring_service.calculate_overall_score(
            crime_data={},
            cost_data=cost(70),
            noise_data=noise(70),
        )
        assert result["component_scores"]["safety"]["score"] == 70.0


# ── _score_to_grade ───────────────────────────────────────────────────────────

class TestScoreToGrade:
    svc = ScoringService()

    @pytest.mark.parametrize("score,expected", [
        (100, "A+"), (90, "A+"),
        (89.9, "A"),  (85, "A"),
        (84.9, "A-"), (80, "A-"),
        (79.9, "B+"), (75, "B+"),
        (74.9, "B"),  (70, "B"),
        (69.9, "B-"), (65, "B-"),
        (64.9, "C+"), (60, "C+"),
        (59.9, "C"),  (55, "C"),
        (54.9, "C-"), (50, "C-"),
        (49.9, "D"),  (0, "D"),
    ])
    def test_grade_boundaries(self, score, expected):
        assert self.svc._score_to_grade(score) == expected


# ── _get_score_status ─────────────────────────────────────────────────────────

class TestGetScoreStatus:
    svc = ScoringService()

    @pytest.mark.parametrize("score,expected", [
        (100, "Excellent"), (80, "Excellent"),
        (79, "Good"),       (70, "Good"),
        (69, "Fair"),       (60, "Fair"),
        (59, "Needs Attention"), (50, "Needs Attention"),
        (49, "Concerning"), (0, "Concerning"),
    ])
    def test_status_labels(self, score, expected):
        assert self.svc._get_score_status(score) == expected


# ── _identify_strengths ───────────────────────────────────────────────────────

class TestIdentifyStrengths:
    svc = ScoringService()

    def test_all_high_returns_all_categories(self):
        strengths = self.svc._identify_strengths(80, 90, 85, 75, 76)
        assert set(strengths) == {"Safety", "Affordability", "Environment", "Lifestyle", "Convenience"}

    def test_all_below_threshold_returns_empty(self):
        assert self.svc._identify_strengths(74, 74, 74, 74, 74) == []

    def test_boundary_74_excluded(self):
        assert "Safety" not in self.svc._identify_strengths(74, 70, 70, 70, 70)

    def test_boundary_75_included(self):
        assert "Safety" in self.svc._identify_strengths(75, 70, 70, 70, 70)

    def test_sorted_descending_by_score(self):
        # Environment=90 > Convenience=85 > Affordability=80 > Safety=76 > Lifestyle=75
        strengths = self.svc._identify_strengths(76, 80, 90, 75, 85)
        assert strengths[0] == "Environment"
        assert strengths[-1] == "Lifestyle"

    def test_single_strength(self):
        strengths = self.svc._identify_strengths(75, 50, 50, 50, 50)
        assert strengths == ["Safety"]


# ── _identify_concerns ────────────────────────────────────────────────────────

class TestIdentifyConcerns:
    svc = ScoringService()

    def test_all_high_no_concerns(self):
        assert self.svc._identify_concerns(80, 80, 80, 80, 80) == []

    def test_low_score_is_concern(self):
        concerns = self.svc._identify_concerns(30, 80, 80, 80, 80)
        assert len(concerns) == 1
        assert concerns[0]["area"] == "Safety"
        assert concerns[0]["score"] == 30

    def test_boundary_60_not_a_concern(self):
        concerns = self.svc._identify_concerns(60, 70, 70, 70, 70)
        assert not any(c["area"] == "Safety" for c in concerns)

    def test_boundary_59_is_a_concern(self):
        concerns = self.svc._identify_concerns(59, 70, 70, 70, 70)
        assert any(c["area"] == "Safety" for c in concerns)

    def test_sorted_ascending_by_score(self):
        concerns = self.svc._identify_concerns(10, 20, 50, 30, 40)
        scores = [c["score"] for c in concerns]
        assert scores == sorted(scores)

    def test_multiple_concerns_identified(self):
        concerns = self.svc._identify_concerns(30, 40, 50, 70, 80)
        areas = {c["area"] for c in concerns}
        assert "Safety" in areas
        assert "Affordability" in areas
        assert "Environment" in areas

    def test_zero_score_is_concern(self):
        concerns = self.svc._identify_concerns(0, 80, 80, 80, 80)
        assert any(c["area"] == "Safety" and c["score"] == 0 for c in concerns)


# ── strengths / concerns in full result ──────────────────────────────────────

class TestStrengthsAndConcernsIntegration:
    def test_strengths_in_overall_result(self):
        result = full_score(safety=90, affordability=80, environment=50,
                            lifestyle=40, convenience=75)
        assert "Safety" in result["strengths"]
        assert "Affordability" in result["strengths"]
        assert "Convenience" in result["strengths"]

    def test_concerns_in_overall_result(self):
        result = full_score(safety=90, affordability=80, environment=50,
                            lifestyle=40, convenience=75)
        concern_areas = {c["area"] for c in result["concerns"]}
        assert "Environment" in concern_areas
        assert "Lifestyle" in concern_areas

    def test_no_overlap_between_strengths_and_concerns(self):
        result = full_score(safety=85, affordability=55, environment=75,
                            lifestyle=45, convenience=90)
        strength_set = set(result["strengths"])
        concern_set = {c["area"] for c in result["concerns"]}
        assert strength_set.isdisjoint(concern_set)
