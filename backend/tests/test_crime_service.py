"""Unit tests for CrimeService — pure helpers + mocked FBI API."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.crime_service import CrimeService, _HOUR_WEIGHTS, _TOTAL_WEIGHT


@pytest.fixture
def svc():
    return CrimeService()


def make_fbi(total=3500.0, violent=None, larceny=None, burglary=None, property_=None,
             source="FBI UCR 2022"):
    return {
        "total": total, "violent": violent, "larceny": larceny,
        "burglary": burglary, "property": property_, "source": source,
    }


# ── _parse_hour_range ─────────────────────────────────────────────────────────

class TestParseHourRange:
    def test_simple_range(self, svc):
        assert svc._parse_hour_range("9:00 - 17:00") == set(range(9, 17))

    def test_midnight_wrap(self, svc):
        result = svc._parse_hour_range("23:00 - 07:00")
        assert result == set(range(23, 24)) | set(range(0, 7))

    def test_same_start_end_midnight(self, svc):
        result = svc._parse_hour_range("0:00 - 8:00")
        assert result == set(range(0, 8))

    def test_invalid_format_returns_empty(self, svc):
        assert svc._parse_hour_range("invalid") == set()

    def test_missing_separator_returns_empty(self, svc):
        assert svc._parse_hour_range("9:0017:00") == set()


# ── _state_from_address ───────────────────────────────────────────────────────

class TestStateFromAddress:
    def test_extracts_state_code(self, svc):
        assert svc._state_from_address("Atlanta, GA 30303, USA") == "GA"

    def test_returns_none_for_us_code(self, svc):
        assert svc._state_from_address("123 Main St, US") is None

    def test_returns_none_when_no_state(self, svc):
        assert svc._state_from_address("no state here") is None

    def test_multiple_commas(self, svc):
        assert svc._state_from_address("123 Main, Chicago, IL, USA") == "IL"


# ── _extract_rate ─────────────────────────────────────────────────────────────

class TestExtractRate:
    def test_valid_response(self, svc):
        data = {"offenses": {"rates": {"State Offenses": {"01-2023": 32.0, "02-2023": 28.0}}}}
        result = svc._extract_rate(data)
        assert result == 60.0

    def test_none_returns_none(self, svc):
        assert svc._extract_rate(None) is None

    def test_missing_offenses_key(self, svc):
        assert svc._extract_rate({}) is None

    def test_empty_rates(self, svc):
        assert svc._extract_rate({"offenses": {"rates": {}}}) is None

    def test_zero_values_excluded(self, svc):
        data = {"offenses": {"rates": {"State Offenses": {"01-2023": 0.0, "02-2023": 0.0}}}}
        assert svc._extract_rate(data) is None

    def test_mixed_valid_and_zero(self, svc):
        data = {"offenses": {"rates": {"State Offenses": {"01-2023": 50.0, "02-2023": 0.0}}}}
        assert svc._extract_rate(data) == 50.0


# ── _static_rate ──────────────────────────────────────────────────────────────

class TestStaticRate:
    def test_known_city(self, svc):
        assert svc._static_rate("downtown chicago") == 5218.0

    def test_known_state(self, svc):
        assert svc._static_rate("Smallville, KS 66002") == 3400.0

    def test_national_average_fallback(self, svc):
        assert svc._static_rate("Unknown Town, ZZ") == 3500.0

    def test_city_takes_priority_over_state(self, svc):
        # New York city rate (2331) vs NY state rate (2800)
        assert svc._static_rate("New York, NY") == 2331.0


# ── _rate_to_safety_score ────────────────────────────────────────────────────

class TestRateToSafetyScore:
    @pytest.mark.parametrize("rate,expected", [
        (1000, 90.0), (1499, 90.0),
        (1500, 80.0), (2499, 80.0),
        (2500, 70.0), (3499, 70.0),
        (3500, 60.0), (4499, 60.0),
        (4500, 50.0), (5499, 50.0),
        (5500, 40.0), (6499, 40.0),
        (6500, 30.0), (7499, 30.0),
        (7500, 20.0), (9999, 20.0),
    ])
    def test_score_tiers(self, svc, rate, expected):
        assert svc._rate_to_safety_score(rate) == expected


# ── _build_location_data ──────────────────────────────────────────────────────

class TestBuildLocationData:
    def test_returns_required_keys(self, svc):
        result = svc._build_location_data(make_fbi())
        for key in ("total_crimes", "daily_average", "crime_rate_per_100k",
                    "safety_score", "categories", "temporal_analysis"):
            assert key in result

    def test_total_crimes_scaled_to_local_pop(self, svc):
        from app.services.crime_service import _LOCAL_POP
        fbi = make_fbi(total=3600.0)
        result = svc._build_location_data(fbi)
        expected = round(3600 / 100_000 * _LOCAL_POP / 12)
        assert result["total_crimes"] == expected

    def test_daily_average_is_total_divided_30(self, svc):
        result = svc._build_location_data(make_fbi())
        assert abs(result["daily_average"] - result["total_crimes"] / 30) < 0.01

    def test_hourly_distribution_length(self, svc):
        result = svc._build_location_data(make_fbi())
        assert len(result["temporal_analysis"]["hourly_distribution"]) == 24

    def test_categories_present(self, svc):
        result = svc._build_location_data(make_fbi())
        for cat in ("violent", "larceny", "burglary", "other_property", "other"):
            assert cat in result["categories"]

    def test_with_fbi_category_rates(self, svc):
        fbi = make_fbi(total=4000.0, violent=800.0, larceny=1500.0, burglary=400.0)
        result = svc._build_location_data(fbi)
        assert result["categories"]["violent"] > 0
        assert result["categories"]["larceny"] > 0

    def test_custom_sleep_hours(self, svc):
        prefs = {"sleep_hours": "22:00 - 06:00", "work_hours": "8:00 - 16:00"}
        result = svc._build_location_data(make_fbi(), user_preferences=prefs)
        assert result["temporal_analysis"]["crimes_during_sleep_hours"] > 0

    def test_midnight_wrap_sleep_hours(self, svc):
        prefs = {"sleep_hours": "23:00 - 07:00"}
        r = svc._build_location_data(make_fbi(), user_preferences=prefs)
        assert r["temporal_analysis"]["crimes_during_sleep_hours"] > 0

    def test_peak_hours_above_threshold(self, svc):
        result = svc._build_location_data(make_fbi())
        hourly = result["temporal_analysis"]["hourly_distribution"]
        peak = result["temporal_analysis"]["peak_hours"]
        max_h = max(hourly)
        threshold = max_h * 0.7
        for h in peak:
            assert hourly[h] >= threshold

    def test_property_derived_from_fbi_when_available(self, svc):
        fbi = make_fbi(total=4000.0, violent=500.0, property_=3500.0,
                       larceny=2000.0, burglary=500.0)
        result = svc._build_location_data(fbi)
        # other_property = property - larceny - burglary, all converted to local pop
        assert result["categories"]["other_property"] >= 0


# ── _recommendation ───────────────────────────────────────────────────────────

class TestRecommendation:
    def test_significantly_safer(self, svc):
        msg = svc._recommendation(50.0, 70.0, 2500.0)
        assert "significantly safer" in msg.lower()

    def test_slightly_safer(self, svc):
        msg = svc._recommendation(65.0, 70.0, 3000.0)
        assert "slightly safer" in msg.lower()

    def test_similar_safety(self, svc):
        msg = svc._recommendation(70.0, 65.0, 3500.0)
        assert "similar" in msg.lower()

    def test_higher_crime(self, svc):
        msg = svc._recommendation(80.0, 50.0, 6000.0)
        assert "higher crime" in msg.lower()


# ── _fetch_fbi_rates (mocked httpx) ──────────────────────────────────────────

def make_httpx_mock(violent_data, property_data, larceny_data=None, burglary_data=None,
                    status=200):
    """Build a mock httpx async client that returns the given data."""
    def make_resp(data):
        r = MagicMock()
        r.status_code = status
        r.json.return_value = data
        return r

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=[
        make_resp(violent_data),
        make_resp(property_data),
        make_resp(larceny_data or {}),
        make_resp(burglary_data or {}),
    ])
    return mock_client


VALID_FBI_RESPONSE = {
    "offenses": {"rates": {"State Offenses": {"01-2023": 32.0, "02-2023": 28.0}}}
}


class TestFetchFbiRates:
    async def test_success_returns_dict(self, svc):
        mock_client = make_httpx_mock(VALID_FBI_RESPONSE, VALID_FBI_RESPONSE)
        with patch("httpx.AsyncClient") as MockClass:
            MockClass.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClass.return_value.__aexit__ = AsyncMock(return_value=None)
            result = await svc._fetch_fbi_rates("Atlanta, GA 30303, USA")
        assert result is not None
        assert "total" in result
        assert result["source"].startswith("FBI Crime Data Explorer")

    async def test_no_state_returns_none(self, svc):
        result = await svc._fetch_fbi_rates("no state address here")
        assert result is None

    async def test_both_rates_none_continues_to_next_year(self, svc):
        # Returns empty dict — both rates will be None, so it should retry and eventually return None
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=MagicMock(status_code=200, json=MagicMock(return_value={})))
        with patch("httpx.AsyncClient") as MockClass:
            MockClass.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClass.return_value.__aexit__ = AsyncMock(return_value=None)
            result = await svc._fetch_fbi_rates("Atlanta, GA 30303, USA")
        assert result is None

    async def test_http_error_continues_to_next_year(self, svc):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=Exception("connection refused")
        )
        with patch("httpx.AsyncClient") as MockClass:
            MockClass.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClass.return_value.__aexit__ = AsyncMock(return_value=None)
            result = await svc._fetch_fbi_rates("Atlanta, GA 30303, USA")
        assert result is None


# ── _get_rates ────────────────────────────────────────────────────────────────

class TestGetRates:
    async def test_returns_fbi_when_available(self, svc):
        fbi_result = {"total": 60.0, "violent": 32.0, "property": 28.0,
                      "larceny": None, "burglary": None, "source": "FBI CDE"}
        with patch.object(svc, "_fetch_fbi_rates", AsyncMock(return_value=fbi_result)):
            result = await svc._get_rates("Atlanta, GA")
        assert result["source"] == "FBI CDE"

    async def test_falls_back_to_static_when_fbi_fails(self, svc):
        with patch.object(svc, "_fetch_fbi_rates", AsyncMock(return_value=None)):
            result = await svc._get_rates("Chicago, IL")
        assert "FBI UCR" in result["source"]
        assert result["total"] == 5218.0  # Chicago static rate


# ── compare_crime_data ────────────────────────────────────────────────────────

class TestCompareCrimeData:
    async def test_returns_current_destination_comparison(self, svc):
        fbi = make_fbi(3500.0)
        with patch.object(svc, "_get_rates", AsyncMock(return_value=fbi)):
            result = await svc.compare_crime_data(
                40.7, -74.0, "New York, NY, USA",
                33.7, -84.4, "Atlanta, GA, USA",
            )
        assert "current" in result
        assert "destination" in result
        assert "comparison" in result

    async def test_safer_destination(self, svc):
        safe = make_fbi(1000.0)
        dangerous = make_fbi(7000.0)
        calls = [dangerous, safe]

        async def fake_get_rates(addr):
            return calls.pop(0)

        with patch.object(svc, "_get_rates", side_effect=fake_get_rates):
            result = await svc.compare_crime_data(
                0, 0, "Dangerous City", 0, 0, "Safe City"
            )
        assert result["comparison"]["is_safer"] is True
        assert result["comparison"]["score_difference"] > 0

    async def test_comparison_fields_present(self, svc):
        fbi = make_fbi(3500.0)
        with patch.object(svc, "_get_rates", AsyncMock(return_value=fbi)):
            result = await svc.compare_crime_data(
                0, 0, "A", 0, 0, "B"
            )
        for key in ("crime_difference", "crime_change_percent", "score_difference",
                    "is_safer", "recommendation"):
            assert key in result["comparison"]
