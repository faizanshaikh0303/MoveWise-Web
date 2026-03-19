"""Unit tests for CostService — pure Python, no external calls."""
import pytest
from app.services.cost_service import CostService, _NATIONAL_MEDIAN, _RATIOS, _HOUSING_RATIO

svc = CostService()


class TestTotalMonthly:
    def test_known_city_exact_match(self):
        assert svc._total_monthly("123 Main St, New York, NY") == 4800.0

    def test_known_city_case_insensitive(self):
        assert svc._total_monthly("downtown manhattan area") == 5500.0

    def test_known_city_substring(self):
        assert svc._total_monthly("456 Oak Ave, Boston, MA 02101") == 4300.0

    def test_state_fallback_when_city_unknown(self):
        assert svc._total_monthly("Rural Town, TX 79000") == 2800.0

    def test_national_median_when_no_match(self):
        assert svc._total_monthly("123 Unknown Rd, ZZ 99999") == _NATIONAL_MEDIAN

    def test_national_median_for_empty_string(self):
        assert svc._total_monthly("") == _NATIONAL_MEDIAN

    def test_high_cost_city_san_francisco(self):
        assert svc._total_monthly("Market St, San Francisco, CA") == 5200.0

    def test_state_code_extracted_from_address(self):
        # Address has no matching city — should fall back to state
        assert svc._total_monthly("Smallville, KS 66002") == 2400.0


class TestAffordabilityScore:
    def test_very_cheap_ratio_below_0_70(self):
        total = _NATIONAL_MEDIAN * 0.60
        assert svc._affordability_score(total) == 100.0

    def test_cheap_ratio_0_85(self):
        total = _NATIONAL_MEDIAN * 0.80
        assert svc._affordability_score(total) == 90.0

    def test_at_median(self):
        assert svc._affordability_score(_NATIONAL_MEDIAN) == 80.0

    def test_slightly_above_median(self):
        total = _NATIONAL_MEDIAN * 1.10
        assert svc._affordability_score(total) == 70.0

    def test_ratio_1_30(self):
        total = _NATIONAL_MEDIAN * 1.25
        assert svc._affordability_score(total) == 60.0

    def test_ratio_1_50(self):
        total = _NATIONAL_MEDIAN * 1.45
        assert svc._affordability_score(total) == 50.0

    def test_ratio_1_70(self):
        total = _NATIONAL_MEDIAN * 1.65
        assert svc._affordability_score(total) == 40.0

    def test_very_expensive_returns_at_least_20(self):
        assert svc._affordability_score(_NATIONAL_MEDIAN * 3.0) >= 20.0

    def test_score_decreases_as_cost_rises(self):
        scores = [svc._affordability_score(_NATIONAL_MEDIAN * r) for r in [0.6, 0.9, 1.1, 1.4, 1.6, 2.0]]
        assert scores == sorted(scores, reverse=True)


class TestRecommendation:
    def test_great_savings(self):
        msg = svc._recommendation(-500, -16.7)
        assert "save" in msg.lower()
        assert "invest" in msg.lower()

    def test_small_savings(self):
        msg = svc._recommendation(-100, -3.3)
        assert "save" in msg.lower()

    def test_manageable_increase(self):
        msg = svc._recommendation(100, 3.3)
        assert "manageable" in msg.lower()

    def test_significant_increase(self):
        msg = svc._recommendation(300, 10.0)
        assert "significant" in msg.lower() or "increase" in msg.lower()

    def test_major_increase(self):
        msg = svc._recommendation(800, 26.7)
        assert "major" in msg.lower()


class TestBuildLocation:
    def test_returns_required_keys(self):
        loc = svc._build_location("New York, NY")
        for key in ("total_monthly", "total_annual", "affordability_score",
                    "cost_index", "housing", "expenses"):
            assert key in loc

    def test_annual_equals_monthly_times_12(self):
        loc = svc._build_location("Chicago, IL")
        assert abs(loc["total_annual"] - loc["total_monthly"] * 12) < 0.1

    def test_expense_ratios_correct(self):
        loc = svc._build_location("Austin, TX")
        total = loc["total_monthly"]
        for key, ratio in _RATIOS.items():
            assert abs(loc["expenses"][key] - round(total * ratio, 2)) < 0.01

    def test_housing_ratio_correct(self):
        loc = svc._build_location("Denver, CO")
        total = loc["total_monthly"]
        expected_rent = round(total * _HOUSING_RATIO, 2)
        assert abs(loc["housing"]["monthly_rent"] - expected_rent) < 0.01

    def test_cost_index_is_ratio_to_median(self):
        loc = svc._build_location("Memphis, TN")
        expected = round(loc["total_monthly"] / _NATIONAL_MEDIAN, 2)
        assert loc["cost_index"] == expected


class TestCompareCosts:
    def test_returns_current_destination_comparison(self):
        result = svc.compare_costs("New York, NY", "Memphis, TN")
        assert "current" in result
        assert "destination" in result
        assert "comparison" in result

    def test_cheaper_destination_is_not_more_expensive(self):
        result = svc.compare_costs("San Francisco, CA", "Memphis, TN")
        assert result["comparison"]["is_more_expensive"] is False
        assert result["comparison"]["monthly_difference"] < 0

    def test_pricier_destination_is_more_expensive(self):
        result = svc.compare_costs("Memphis, TN", "San Francisco, CA")
        assert result["comparison"]["is_more_expensive"] is True
        assert result["comparison"]["monthly_difference"] > 0

    def test_same_city_zero_difference(self):
        result = svc.compare_costs("Chicago, IL", "Chicago, IL")
        assert result["comparison"]["monthly_difference"] == 0.0
        assert result["comparison"]["percent_change"] == 0.0

    def test_annual_difference_is_monthly_times_12(self):
        result = svc.compare_costs("Austin, TX", "Seattle, WA")
        assert abs(result["comparison"]["annual_difference"] -
                   result["comparison"]["monthly_difference"] * 12) < 0.1

    def test_score_difference_matches_components(self):
        result = svc.compare_costs("New York, NY", "Detroit, MI")
        expected_diff = (result["destination"]["affordability_score"] -
                         result["current"]["affordability_score"])
        assert abs(result["comparison"]["score_difference"] - expected_diff) < 0.01

    def test_percent_change_sign_matches_direction(self):
        result_more = svc.compare_costs("Memphis, TN", "New York, NY")
        result_less = svc.compare_costs("New York, NY", "Memphis, TN")
        assert result_more["comparison"]["percent_change"] > 0
        assert result_less["comparison"]["percent_change"] < 0
